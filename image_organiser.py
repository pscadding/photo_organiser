#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys
import logging
import pprint
import exifread
from datetime import datetime

logger = logging.getLogger('Photo_Organiser')
logging.basicConfig()
logger.setLevel(logging.DEBUG)

tag_match_list = ['Holiday','Events','Outings','Birthday']

root_path = r"F:\Users\Pictures\Photos\Holidays"



def find_tags(aFile, tag_list):
    fd = open(file_path, encoding="Latin-1")
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

for root, folders, files in os.walk(root_path):
    logger.info("Root: %s" % root)
    for aFile in files:
        file_path = os.path.join(root,aFile)
        logger.info("%s" % file_path)

        tags = find_tags(file_path,tag_match_list)

        f = open(file_path, 'rb')

        # Return Exif tags
        exif_tags = exifread.process_file(f)
        # pprint.pprint(exif_tags)

        logger.debug("Tags: %s" % tags)
        get_date_time(exif_tags)
        logger.info("\n\n\n")

