#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys
import logging
import pprint
import exifread
from collections import defaultdict
from datetime import datetime

logger = logging.getLogger('Photo_Organiser')
logging.basicConfig(stream=sys.stdout)
logger.setLevel(logging.DEBUG)


tag_match_list = ['Holiday','Events','Outings','Birthday']

root_path = r"F:\Users\Pictures\Photos\Holidays"
# root_path = r"/Volumes/Seagate Expansion Drive/Users/Pictures/Photos/Holidays"
dest_folder = r"F:\Users/Pictures/Photos"

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

def construct_new_path(tags,datetime):

    if tags:
        path = os.sep.join([str(datetime.year),datetime.strftime("%B")] + tags)
    else:
        path = datetime.strftime("%Y\\%B\\%d")

    logger.info(path)

    return path

def file_stats():

    file_types = defaultdict(int)

    for root, folders, files in os.walk(root_path):
        for aFile in files:
            file_name, ext = os.path.splitext(aFile)
            file_types[ext.lower()] += 1

    logger.info(pprint.pformat(file_types))

def organise_files():

    for root, folders, files in os.walk(root_path):
        logger.info("Root: %s" % root)

        files_to_copy = defaultdict(dict)

        for aFile in files:
            source_path = os.path.join(root,aFile)

            file_name, ext = os.path.splitext(source_path)
            logger.info("%s" % source_path)

            existing_file = files_to_copy.get(file_name,{}).get('dest')
            files_to_copy[file_name][ext] = aFile

            if existing_file:
                continue


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

            new_path = construct_new_path(tags, date_time)
            new_path = os.path.join(dest_folder, new_path)
            logger.info(new_path)

            files_to_copy[file_name]['dest'] = new_path

            #handle clashes with file name
            logger.info("\n\n\n")

        logger.info(pprint.pformat(files_to_copy))

    logger.info("Files not copied: %s" % files_not_copied)

# file_stats()
organise_files()