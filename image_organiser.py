#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys
import logging
import pprint
import exifread
from datetime import datetime

logger = logging.getLogger('Photo_Organiser')
logging.basicConfig(stream=sys.stdout)
logger.setLevel(logging.DEBUG)


tag_match_list = ['Holiday','Events','Outings','Birthday']

# root_path = r"F:\Users\Pictures\Photos\Holidays"
root_path = r"/Volumes/Seagate Expansion Drive/Users/Pictures/Photos/Holidays"
dest_folder = r"/Volumes/Seagate Expansion Drive/Users/Pictures/Photos"

files_not_copied = []

def find_tags(aFile, tag_list):
    with open(aFile, encoding="Latin-1") as fd:
        d = fd.read()
    xmp_start = d.find('<x:xmpmeta')
    xmp_end = d.find('</x:xmpmeta')
    xmp_str = d[xmp_start:xmp_end + 12]
    xmp_str = xmp_str.lower()
    return [aTag for aTag in tag_list if aTag.lower() in xmp_str ]

def get_date_time(data):
    img_date_time_str = str(data.get('Image DateTime',''))
    exif_digit_date_time_str = str(data.get('EXIF DateTimeDigitized',''))
    exif_orig_date_time_str = str(data.get('EXIF DateTimeOriginal',''))
    date_times = list(set(filter(None,[img_date_time_str,exif_digit_date_time_str,exif_orig_date_time_str])))
    if len(date_times) == 0:
        logger.warning('No Date time!')
        return None
    if len(date_times) > 1:
        logger.warning('Multiple Take dates! %s' % date_times)
        raise ValueError('Multiple Take dates!',date_times)
    datetime_object = datetime.strptime(date_times[0], '%Y:%m:%d  %H:%M:%S')
    logger.debug("%s %s" % (date_times,datetime_object))
    return datetime_object

def construct_new_path(file,tags,datetime):

    if tags:
        path = os.sep.join([str(datetime.year),datetime.strftime("%B")] + tags)
    else:
        path = datetime.strftime("%Y\\%B\\%d")

    path = os.path.join(path,file)
    logger.info(path)

    return path



for root, folders, files in os.walk(root_path):
    logger.info("Root: %s" % root)
    for aFile in files:
        source_path = os.path.join(root,aFile)
        logger.info("%s" % source_path)


        with open(source_path, 'rb') as f:

            tags = find_tags(source_path,tag_match_list)

            # Return Exif tags
            try:
                exif_tags = exifread.process_file(f)
                # pprint.pprint(exif_tags)

                logger.debug("Tags: %s" % tags)
                date_time = get_date_time(exif_tags)
            except OSError as e:
                logger.warning("Failed to read exif data: %s" % e)
                files_not_copied.append(source_path)
                continue

            if date_time is None:
                files_not_copied.append(source_path)
                continue

        new_path = construct_new_path(aFile, tags, date_time)
        new_path = os.path.join(dest_folder,new_path)
        logger.info(new_path)

        #handle clashes with file name


        logger.info("\n\n\n")

logger.info("Files not copied: %s" % files_not_copied)