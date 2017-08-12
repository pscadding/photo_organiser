

s = '''   xmp:CreatorTool="digiKam-5.6.0"
   xmp:MetadataDate="2009-07-23T21:00:09"
   xmp:CreateDate="2009-07-23T21:00:09"
   xmp:ModifyDate="2009-07-23T21:00:09"
   xmp:Rating="2"
   exif:DateTimeOriginal="2009-07-23T21:00:09"
   tiff:DateTime="2009-07-23T21:00:09"
   tiff:Software="digiKam-5.6.0"
   video:DateTimeOriginal="2009-07-23T21:00:09"
   video:DateUTC="2009-07-23T21:00:09"
   video:ModificationDate="2009-07-23T21:00:09"
   digiKam:PickLabel="0"
   digiKam:ColorLabel="0"
   acdsee:rating="2"'''

import re

m = re.search('(?<=DateTimeOriginal=").+(?=")',s)

print(m[0])

b = a = c = 4
