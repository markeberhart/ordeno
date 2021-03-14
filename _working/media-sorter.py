'''
Put this script in a messy folder filled with images and video files 
and run it to create a "Years" folder with the media files sorted by months in each year.

You can also change what types of files to look for in your folder
by simply adding to or changing the following lists: `imgFormats` and `videoFormats`.

NOTE: This script can also delete duplicates (by searcing for " 2" at the end of file names) and files starting with "._".
This is disabled by default, to enable set `DELETE` flag to True!
'''

import os
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS
from hachoir.parser import createParser
from hachoir.metadata import extractMetadata

DATE_TIME_ORIG_TAG = 36867
DELETE = False
rootdir = 'D:\__MY_FILES\Pictures\Camera Roll'

imgFormats = ['png', 'jpg', 'jpeg', 'png']
videoFormats = ['m4v', 'mov', 'mp4']

for subdir, dirs, files in os.walk(rootdir):
    for afile in files:
        targ = os.path.join(subdir, afile)
        filename = os.fsdecode(targ)
        print("Processing %s\n" % filename)
        name = filename.split('.')[0]
        if os.path.isdir(filename):
            continue
        elif name[-2:] == ' 2' and DELETE:
            print("Renaming %s\n" % name)
            ext = filename.split('.')[1]
            try:
                os.rename(filename, name[:-1].strip() + '.' + ext)
            except FileExistsError:
                print("Found existing file %s - Deleting\n" % name)
                os.remove(name[:-1].strip() + '.' + ext)
                os.rename(filename, name[:-1].strip() + '.' + ext)
            continue
        elif filename.endswith(".py"):
            continue
        elif filename.startswith("._") and DELETE:
            print("Deleting %s\n" % filename)
            os.remove(filename)
            continue
        elif filename.split('.')[1].lower() in imgFormats:
            try:
                im = Image.open(afile)
                exif = im._getexif()
                im.close()
                if DATE_TIME_ORIG_TAG in exif:
                    print("Has EXIF: %s\n" % exif[DATE_TIME_ORIG_TAG])
                    datestr = exif[DATE_TIME_ORIG_TAG].split()
                    dateobj = datetime.strptime(datestr[0], "%Y:%m:%d")
                    dirpath = "Years/%s/%s/" % (dateobj.year, dateobj.month)
                    os.makedirs(dirpath, exist_ok=True)
                    os.rename(filename, dirpath + filename)
                continue
            except:
                continue
        elif filename.split('.')[1].lower() in videoFormats:
            parser = createParser(filename)
            if not parser:
                print("Unable to parse file %s" % filename)
                continue
            with parser:
                try:
                    metadata = extractMetadata(parser)
                except Exception as err:
                    print("Metadata extraction error: %s" % err)
                    metadata = None
            if not metadata:
                print("Unable to extract metadata")
                continue
            for line in metadata.exportPlaintext():
                if line.split(':')[0] == '- Creation date':
                    dateobj = datetime.strptime(
                        line.split(':')[1].split()[0], "%Y-%m-%d")
                    dirpath = "Years/%s/%s/" % (dateobj.year, dateobj.month)
                    os.makedirs(dirpath, exist_ok=True)
                    os.rename(filename, dirpath + filename)