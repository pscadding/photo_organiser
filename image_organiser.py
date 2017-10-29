#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys, re
sys.path.append(r"C:\Users\posca\AppData\Local\Programs\Python\Python36\Lib\site-packages\pywin32_system32")
import logging
import pprint
import exifread
from collections import defaultdict
from datetime import datetime
from win32com.propsys import propsys, pscon

logger = logging.getLogger('Photo_Organiser')
logging.basicConfig(stream=sys.stdout)
logger.setLevel(logging.DEBUG)

tag_match_list = ['Holiday', 'Events', 'Outings', 'Birthday', 'Christmas', 'Easter', 'Pilton','Time-lapse']

root_paths = [r'E:\Users\Pictures\Photos\to_be_sorted']
# r'F:\Users\Pictures\Photos\1979',
# r'F:\Users\Pictures\Photos\1980',]
# r'F:\Users\Pictures\Photos\2012',
# r'F:\Users\Pictures\Photos\2011',
# r'F:\Users\Pictures\Photos\2010',
# r'F:\Users\Pictures\Photos\2009',
# r'F:\Users\Pictures\Photos\2008',
# r'F:\Users\Pictures\Photos\2007',
# r'F:\Users\Pictures\Photos\2006',
# r'F:\Users\Pictures\Photos\2005',
# r'F:\Users\Pictures\Photos\2017',]
# root_path = r"/Volumes/Seagate Expansion Drive/Users/Pictures/Photos/Holidays"
dest_folder = r"E:\Users/Pictures/Photos"

files_not_copied = []


def read_data(aFile):
    with open(aFile, encoding="Latin-1") as fd:
        try:
            d = fd.read()
            xmp_start = d.find('<x:xmpmeta')
            xmp_end = d.find('</x:xmpmeta')
            xmp_str = d[xmp_start:xmp_end + 12]
        except MemoryError:
            print("got memory error",fd)
            myfile = open(aFile,encoding="Latin-1")
            xmp_str = ""
            start = False
            for line in myfile:
                if line.find('<x:xmpmeta') != -1:
                    xmp_str += line
                    start = True

                if start:
                    xmp_str += line

                if line.find('</x:xmpmeta') != -1:
                    break
    return xmp_str.lower()


def find_tags(xmp_meta, tag_list):
    return [aTag for aTag in tag_list if aTag.lower() in xmp_meta]


def get_xmp_date_time(xmp_meta):
    logging.info("Reading xmp info for date")
    # mainly usefull for reading video file meta data
    match = re.search('(?<=datetimeoriginal=").+?(?=")', xmp_meta)

    # For Photoshop files
    if not match: match = re.search('(?<=photoshop:datecreated>).+?(?=<)', xmp_meta)
    if not match: match = re.search('(?<=xap:createdate>).+?(?=<)', xmp_meta)
    if not match: match = re.search('(?<=xmp:modifydate=").+?(?=")', xmp_meta)

    if match:
        try:
            datetime_object = datetime.strptime(match[0][:19], '%Y-%m-%dt%H:%M:%S')
        except ValueError:
            try:
                datetime_object = datetime.strptime(match[0][:19], '%Y:%m:%dt%H:%M:%S')
            except ValueError:
                try:
                    datetime_object = datetime.strptime(match[0][:16], '%Y:%m:%dt%H:%M')
                except ValueError:
                    datetime_object = datetime.strptime(match[0][:16], '%Y-%m-%dt%H:%M')

        logger.debug("%s %s" % (match[0][:19], datetime_object))
        return datetime_object

    return None


def get_exif_date_times(meta_data_source):
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

    date_times = list(filter(None, [exif_orig_date_time_str,
                                    date_time_original,
                                    img_date_time_str,
                                    exif_digit_date_time_str, ]))

    return [datetime.strptime(date_times[0], '%Y:%m:%d  %H:%M:%S') for date_time in date_times]


def get_date_time(meta_data_source, source_path, xmp_meta):
    date_times = []

    xmp_date_time = get_xmp_date_time(xmp_meta)
    if xmp_date_time: date_times.append(xmp_date_time)

    date_times += get_exif_date_times(meta_data_source)

    properties = propsys.SHGetPropertyStoreFromParsingName(source_path)
    dt = properties.GetValue(pscon.PKEY_Media_DateEncoded).GetValue()
    if dt: date_times.append(dt)
    else:
        dt = properties.GetValue(pscon.PKEY_DateModified).GetValue()
        if dt: date_times.append(dt)

    if len(date_times) == 0:
        logger.warning('No Date time!')
        return None

    oldest_date_time = date_times[0].replace(tzinfo=None)

    for date_time in date_times:
        date_time = date_time.replace(tzinfo=None)
        oldest_date_time = oldest_date_time if oldest_date_time < date_time else date_time

    return oldest_date_time


def suffix(d):
    return 'th' if 11 <= d <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(d % 10, 'th')


def construct_new_path(tags, datetime):
    if tags:
        path = os.sep.join(
            [str(datetime.year), datetime.strftime("%B")] + tags + [str(datetime.day) + suffix(datetime.day)])
    else:
        path = datetime.strftime("%Y\\%B\\%d") + suffix(datetime.day)

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
                source_file = os.path.join(source_root, image_path)
                logger.info("source_file %s" % source_file)
                dest_file = os.path.join(dest_root, image_path)
                logger.info("dest_file %s" % dest_file)

                success = False
                dest_path = dest_file
                i = 0
                while not success:
                    try:
                        os.rename(source_file, dest_path)
                        success = True
                    except FileExistsError:
                        i += 1
                        file_name, ext = os.path.splitext(image_path)
                        temp_name = os.path.splitext(image_path)[0] + "_" + str(i) + ext
                        dest_path = os.path.join(dest_root, temp_name)


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
                source_path = os.path.join(root, aFile)

                file_name, ext = os.path.splitext(source_path)
                logger.info("File: %s" % source_path)

                if ext in ['.db','.info']:
                    continue

                if 'JpegRotator' in file_name:
                    continue

                if ext != ".xmp":
                    xmp_file = source_path + ".xmp"
                else:
                    # We have an xmp file so we need to strip the extension again to get the original file name
                    # As xmp file are like my_file.jpg.xmp
                    file_name, org_ext = os.path.splitext(file_name)

                meta_data_source = source_path if not os.path.isfile(xmp_file) else xmp_file
                logger.info("Meta Data Source: %s" % meta_data_source)

                """Check if there is already a file with the same name in the folder and if so use the same destination"""
                existing_file = files_to_copy.get(file_name, {}).get('dest')
                files_to_copy[file_name][ext] = aFile

                if existing_file:
                    continue

                xmp_meta = read_data(meta_data_source)

                """Try and find any recognisable standard tags to use in the new path structure"""
                tags = find_tags(xmp_meta, tag_match_list)
                logger.debug("Tags: %s" % tags)

                """Try and find the date the photo was taken"""
                date_time = get_date_time(meta_data_source, source_path, xmp_meta)

                if date_time is None:
                    files_not_copied.append(source_path)
                    continue

                new_path = construct_new_path(tags, date_time)
                new_path = os.path.join(dest_folder, new_path)
                logger.info(new_path)

                files_to_copy[file_name]['dest'] = new_path

                # handle clashes with file name
                logger.info("\n\n\n")

            logger.info(pprint.pformat(files_to_copy))
            copy_files(files_to_copy)

        logger.info("Files not copied: %s" % files_not_copied)


def find_files_with_no_ext():
    """Loop over root paths"""
    for root_path in root_paths:
        """ Walk over the files in the root path"""
        for root, folders, files in os.walk(root_path):

            for aFile in files:
                # print(aFile, len(os.path.splitext(aFile)), os.path.splitext(aFile) )
                if not os.path.splitext(aFile)[1]:
                    print(os.path.join(root, aFile))


def remove_empty_folders():
    for root_path in root_paths:
        """ Walk over the files in the root path"""
        for root, folders, files in os.walk(root_path):
            print("root",root)
            try:
                os.removedirs(root)
            except OSError as ex:
                print("directory not empty",ex)


# file_stats()
organise_files()
# find_files_with_no_ext()
# remove_empty_folders()
