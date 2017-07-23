#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys
import pprint
import exifread

tag_match_list = ['Holiday','Events','Outings','Birthday']

root_path = r"F:\Users\Pictures\meta_data_test"



def find_tags(aFile, tag_list):
    fd = open(file_path, encoding="Latin-1")
    d = fd.read()
    xmp_start = d.find('<x:xmpmeta')
    xmp_end = d.find('</x:xmpmeta')
    xmp_str = d[xmp_start:xmp_end + 12]
    xmp_str = xmp_str.lower()
    return [aTag for aTag in tag_list if aTag.lower() in xmp_str ]

for root, folders, files in os.walk(root_path):
    print ("Root:",root)
    for aFile in files:
        file_path = os.path.join(root,aFile)
        print(file_path)

        tags = find_tags(file_path,tag_match_list)


        f = open(file_path, 'rb')

        # Return Exif tags
        exif_tags = exifread.process_file(f)
        # pprint.pprint(exif_tags)
        print("\n",file_path)
        print(tags)
        print(exif_tags['Image DateTime'])
        print(exif_tags['EXIF DateTimeDigitized'])
        print(exif_tags['EXIF DateTimeOriginal'])
