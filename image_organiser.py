#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys, re
import logging
import pprint
import exifread
from collections import defaultdict
from datetime import datetime

logger = logging.getLogger('Photo_Organiser')
logging.basicConfig(stream=sys.stdout)
logger.setLevel(logging.DEBUG)


tag_match_list = ['Holiday','Events','Outings','Birthday']

root_paths = [r"F:\Users\Pictures\Photos\2005",
              r"F:\Users\Pictures\Photos\2008"]
# root_path = r"/Volumes/Seagate Expansion Drive/Users/Pictures/Photos/Holidays"
dest_folder = r"F:\Users/Pictures/Photos"

files_not_copied = []

def read_data(aFile):
    with open(aFile, encoding="Latin-1") as fd:
        d = fd.read()
    xmp_start = d.find('<x:xmpmeta')
    xmp_end = d.find('</x:xmpmeta')
    xmp_str = d[xmp_start:xmp_end + 12]
    return xmp_str.lower()

def find_tags(aFile, tag_list):
    xmp_str = read_data(aFile)
    return [aTag for aTag in tag_list if aTag.lower() in xmp_str ]

def get_date_time(meta_data_source):
    img_date_time_str = exif_digit_date_time_str = exif_orig_date_time_str = date_time_original = None

    with open(meta_data_source, 'rb') as f:
        # Return Exif tags
        try:
            exif_tags = exifread.process_file(f)
            img_date_time_str = str(exif_tags.get('Image DateTime', ''))
            exif_digit_date_time_str = str(exif_tags.get('EXIF DateTimeDigitized', ''))
            exif_orig_date_time_str = str(exif_tags.get('EXIF DateTimeOriginal', ''))
        except OSError as e:
            logger.warning("Failed to read exif data: %s" % e)


    date_times = list(set(filter(None,[img_date_time_str,
                                       exif_digit_date_time_str,
                                       exif_orig_date_time_str,
                                       date_time_original])))
    if len(date_times) == 0:
        logging.info("Reading xmp info for date")
        xmp_str = read_data(meta_data_source)
        match = re.search('(?<=datetimeoriginal=").+(?=")', xmp_str)
        if not match:
            logger.warning('No Date time!')
            return None

        datetime_object = datetime.strptime(match[0], '%Y-%m-%dt%H:%M:%S')
        logger.debug("%s %s" % (match[0], datetime_object))
    else:
        datetime_object = datetime.strptime(date_times[0], '%Y:%m:%d  %H:%M:%S')
        logger.debug("%s %s" % (date_times, datetime_object))

    if len(date_times) > 1:
        logger.warning('Multiple Take dates! %s' % date_times)
        # raise ValueError('Multiple Take dates!',date_times)


    return datetime_object

def construct_new_path(tags,datetime):

    if tags:
        path = os.sep.join([str(datetime.year),datetime.strftime("%B")] + tags + [datetime.strftime("%d")])
    else:
        path = datetime.strftime("%Y\\%B\\%d")

    logger.info(path)

    return path

def file_stats():

    file_types = defaultdict(int)

    for root_path in root_paths:

        for root, folders, files in os.walk(root_path):
            for aFile in files:
                file_name, ext = os.path.splitext(aFile)
                file_types[ext.lower()] += 1

    logger.info(pprint.pformat(file_types))

def copy_files(files_to_copy):

    for path, images in files_to_copy.items():

        source_root = os.path.dirname(path)
        dest_root = images.get('dest')

        if not dest_root: continue

        if not os.path.exists(dest_root):
            os.makedirs(dest_root)

        for img_type, image_path in images.items():
            if img_type != "dest":
                source_file = os.path.join(source_root,image_path)
                logger.info("source_file %s" % source_file)
                dest_file = os.path.join(dest_root,image_path)
                logger.info("dest_file %s" % dest_file)
                try:
                    os.rename(source_file,dest_file)
                except FileExistsError:
                    image_path = os.path.splitext(image_path)[0] + "_1"
                    dest_file = os.path.join(dest_root, image_path)
                    os.rename(source_file, dest_file)



def organise_files():

    """Loop over root paths"""
    for root_path in root_paths:

        """ Walk over the files in the root path"""
        for root, folders, files in os.walk(root_path):
            logger.info("Root: %s" % root)

            """For each folder gather a dictionary of files to copy"""
            files_to_copy = defaultdict(dict)

            """Loop over the files in the folder"""
            for aFile in files:
                source_path = os.path.join(root,aFile)

                file_name, ext = os.path.splitext(source_path)
                logger.info("File: %s" % source_path)

                xmp_file = source_path + ".xmp"
                meta_data_source = source_path if not os.path.isfile(xmp_file) else xmp_file
                logger.info("Meta Data Source: %s" % meta_data_source)

                """Check if there is already a file with the same name in the folder and if so use the same destination"""
                existing_file = files_to_copy.get(file_name,{}).get('dest')
                files_to_copy[file_name][ext] = aFile

                if existing_file:
                    continue

                """Try and find any recognisable standard tags to use in the new path structure"""
                tags = find_tags(meta_data_source, tag_match_list)
                logger.debug("Tags: %s" % tags)

                """Try and find the date the photo was taken"""
                date_time = get_date_time(meta_data_source)

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
            copy_files(files_to_copy)

        logger.info("Files not copied: %s" % files_not_copied)

# file_stats()
organise_files()