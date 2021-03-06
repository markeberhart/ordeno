#import PySimpleGUI as sg
import exifread
import os, time
import warnings
from datetime import datetime
import shutil
import pathlib
import csv
import hashlib
import pickle

from hachoir.parser import createParser
from hachoir.metadata import extractMetadata
from hachoir.core import config as HachoirConfig
HachoirConfig.quiet = True

#C:\Python38\python.exe <- use this as interpreter when not working

#warnings.filterwarnings("ignore")
#from pymediainfo import MediaInfo
#import cv2

# todo - check duplicates simply by looking at hash table and not looking or file existing?

#copyfromdir = sg.popup_get_folder('Enter the file you wish to process')
#This PC\Apple iPhone\Internal Storage\DCIM\100CLOUD
#E:\berenice_iphone   'E:\\berenice_iphone\\by_date'
#D:\\__MY_FILES\\Pictures\\iCloud Photos
#D:\\__MY_FILES\\Pictures\\by_date
#D:\__MY_FILES\Pictures\Camera Roll
hash_set = set()
reset_hash_set = False
hash_set_log = 'D:\\__MY_FILES\\Pictures\\Camera Roll\\rgb\\hash_set_log.data'
log_copied = 'D:\\__MY_FILES\\Pictures\\Camera Roll\\rgb\\log_copied_rgb.csv'
log_not_copied = 'D:\\__MY_FILES\\Pictures\\Camera Roll\\rgb\\log_not_copied_rgb.csv'
copyfromdir = 'D:\\__MY_FILES\\Pictures\\Camera Roll\\rgb'
copytodir = 'D:\\__MY_FILES\\Pictures\\Camera Roll\\rgb\\by_date'



# popwin = sg.popup('You entered', picdir)
IMAGE_TYPES = ('png', 'jpeg', 'jpg', 'gif', 'JPG', 'JPEG','PNG', 'mov', 'MOV', 'm4v', 'M4V', 'mp4','MP4','wmv', 'WMV', 'avi', 'AVI')
print("===========================================")
print(copyfromdir)

epoch = datetime.utcfromtimestamp(0)

def add_to_copied_log(fields):
    #hash_set
    with open(log_copied, 'a', newline='') as csvfile: 
        # creating a csv writer object 
        csvwriter = csv.writer(csvfile) 
        # writing the fields 
        csvwriter.writerow(fields)

def add_to_not_copied_log(fields):
    #hash_set
    with open(log_not_copied, 'a', newline='') as csvfile: 
        # creating a csv writer object 
        csvwriter = csv.writer(csvfile) 
        # writing the fields 
        csvwriter.writerow(fields)

def create_copied_log():
    # field names 
    fields = ['original_file', 'new_file', 'type', 'date', 'ms', 'was_copied', 'hash']
    with open(log_copied, 'w', newline='') as csvfile:
        # creating a csv writer object
        csvwriter = csv.writer(csvfile)
        # writing the fields 
        csvwriter.writerow(fields)

def create_not_copied_log():
    # field names 
    fields = ['original_file', 'new_file', 'type', 'date', 'ms', 'was_copied', 'hash']
    with open(log_not_copied, 'w', newline='') as csvfile: 
        # creating a csv writer object 
        csvwriter = csv.writer(csvfile) 
        # writing the fields 
        csvwriter.writerow(fields)

def create_hash_set_log():
    with open(hash_set_log, 'wb') as filehandle:
        _set = set()
        pickle.dump(_set, filehandle)
        return _set

def save_hash_set_log():
    with open(hash_set_log, 'wb') as filehandle:
        _set = hash_set
        pickle.dump(_set, filehandle)
        return _set

def get_hash_set_log():
    with open(hash_set_log, 'rb') as filehandle:
        _set = pickle.load(filehandle)
        return _set

def hash_set_log_exists():
    exists = False
    if os.path.isfile(hash_set_log):
        exists = True
    return exists

def delete_hash_set_log():
    os.remove(hash_set_log)

def try_load_hash_set_log():
    if(hash_set_log_exists()):
        if(reset_hash_set):
            delete_hash_set_log()
            hash_set = create_hash_set_log()
        else:
            hash_set = get_hash_set_log()
    else: 
        hash_set = create_hash_set_log()
    return hash_set

def addto_hash_set(img_hash):
    hash_set.add(img_hash)

def unix_time_millis(dt):
    return (dt - epoch).total_seconds() * 1000.0

def get_mod_date(file):
    modtime = int(os.path.getmtime(file))
    moddate = datetime.fromtimestamp(modtime)
    obj = {
        'year':   str(moddate.year),
        'month':  str(moddate.month),
        'day':    str(moddate.day),
        'hour':   add_zero(str(moddate.hour)),
        'minute':   add_zero(str(moddate.minute)),
        'ms':     modtime*1000,
        'type': 'md'
    }
    return obj

def get_cdate_date(dt):
    dtoms = datetime.strptime(dt, '%Y-%m-%d %H:%M:%S')
    dt2 = unix_time_millis(dtoms)
    obj = {
        'year':   str(dtoms.year),
        'month':  str(dtoms.month),
        'day':    str(dtoms.day),
        'hour':   add_zero(str(dtoms.hour)),
        'minute':   add_zero(str(dtoms.minute)),
        'ms':     int(dt2),
        'type': 'cd'
    }
    return obj

def get_exif_date(dt):
    try:
        dtoms = datetime.strptime(dt, '%Y:%m:%d %H:%M:%S')
        dt2 = unix_time_millis(dtoms)
        obj = {
            'year':   str(dtoms.year),
            'month':  str(dtoms.month),
            'day':    str(dtoms.day),
            'hour':   add_zero(str(dtoms.hour)),
            'minute':   add_zero(str(dtoms.minute)),
            'ms':     int(dt2),
            'type': 'dto'
        }
        return obj
    except ValueError:
        obj = {
            'year':   '9999',
            'month':  '99',
            'day':    '99',
            'hour':   '99',
            'minute': '99',
            'ms':     '999999999999988'
        }
        return obj

def get_earliest_date(arr):
    dates_by_ms = {}
    min_val = 999999999999999
    for date in arr:
        ms = str(date['ms'])
        dates_by_ms[ms] = date
        msnum = int(ms)
        if min_val > msnum and msnum > 0:
            min_val = msnum
    obj = dates_by_ms[str(min_val)]
    return obj

def create_dir(str):
    try:
        os.makedirs(str)
        print("  -> TRY CREATE: " + str)
    except FileExistsError:
        # directory already exists
        pass

def add_zero(str):
    strlen = len(str)  
    if(strlen==1):
        str="0"+str
    return str

def get_date_str_obj(obj):
    year = str(obj['year'])
    month = add_zero(str(obj['month']))
    day = add_zero(str(obj['day']))
    hour = add_zero(str(obj['hour']))
    minute = add_zero(str(obj['minute']))
    ms = str(obj['ms'])
    new_obj = {
        'year':   year,
        'month':  month,
        'day':    day,
        'hour':   hour,
        'minute': minute,
        'ms':     ms
    }
    return new_obj

def get_date_str(obj):
    return obj['year']+"-"+obj['month']+"-"+obj['day']

def create_dates_dir(obj):
    dir_year    = copytodir+"\\"+ obj['year']
    dir_month   = dir_year+"\\"+ obj['month']
    dir_day     = dir_month+"\\"+ obj['day']
    date_arr = [dir_year, dir_month, dir_day]
    for d in date_arr:
        create_dir(d)
    return dir_day

def copy_file(targ, dest):
    shutil.copy2(targ, dest)

def make_a_copy(targ, dest, img_hash, fields):
    add_to_copied_log(fields)
    copy_file(targ, dest)
    addto_hash_set(img_hash)
    print("ORIG  FILE:" + targ)
    print("NEW FILE:" + dest)

def dont_make_a_copy(targ, dest, img_hash, fields):
    add_to_not_copied_log(fields)
    #copy_file(targ, dest)
    #addto_hash_set(img_hash)
    print("NOT COPIED:" + targ)

def get_new_filename(obj, ext, img_hash):
    new_name = obj['year']
    new_name = new_name + "-" + obj['month']
    new_name = new_name + "-" + obj['day']
    new_name = new_name + "_" + obj['hour']
    new_name = new_name + obj['minute']
    new_name = new_name + "_" + obj['ms']
    new_name = new_name + "_" + img_hash
    new_name = new_name + ext
    return new_name

def try_add_new_file(dates_array, targ, ext, img_hash):
    earliest_date = get_earliest_date(dates_array)
    str_date_obj = get_date_str_obj(earliest_date)
    day_dir = create_dates_dir(str_date_obj)
    new_file = get_new_filename(str_date_obj, ext, img_hash)
    dest = day_dir+"\\"+new_file
    new_file = dest

    # log file fields
    file_orig = targ
    file_type = ext.lower()
    date = get_date_str(str_date_obj)
    ms = str_date_obj['ms']
    print("HASH: " + img_hash)
    print ("HASH SET: " + str(hash_set))

    # NO Image date not previousy encountered
    # NO Image with these pixels not encountered
    if (not os.path.isfile(dest) and img_hash not in hash_set):
        fields = [file_orig, new_file, file_type, date, ms, 'true', img_hash]
        make_a_copy(targ, dest,img_hash,fields)
        
    # YES Image date previousy encountered
    # NO Image with these pixels not encountered
    elif (os.path.isfile(dest) and img_hash not in hash_set):
        fields = [file_orig, new_file, file_type, date, ms, 'true', img_hash]
        make_a_copy(targ, dest,img_hash,fields)

    # NO Image date not previousy encountered
    # YES Image with these pixels encountered
    # todo what about when images deleted, but corresponding hash record not deleted in .data file?
    elif (not os.path.isfile(dest) and img_hash in hash_set):
        fields = [file_orig, new_file, file_type, date, ms, 'false', img_hash]
        dont_make_a_copy(targ, dest,img_hash,fields)

    # YES Image date not previousy encountered
    # YES Image with these pixels encountered
    elif (os.path.isfile(dest) and img_hash in hash_set):
        fields = [file_orig, new_file, file_type, date, ms, 'false', img_hash]
        dont_make_a_copy(targ, dest,img_hash,fields)

    else:
        fields = [file_orig, new_file, file_type, date, ms, 'false', img_hash]
        dont_make_a_copy(targ, dest,img_hash,fields)
        

def main():
    create_copied_log()
    create_not_copied_log()
    for subdir, dirs, files in os.walk(copyfromdir):
        for file in files:
            dates_array = []
            targ = os.path.join(subdir, file)
            ext = os.path.splitext(file)[1]
            #print(os.path.join(subdir, file))
            date_type = 'md'
            dt1 = get_mod_date(targ)
            dates_array.append(dt1)
            img_hash = ''
            if targ.endswith(IMAGE_TYPES):
                print(file + " | " + ext)
                
                with open(targ, 'rb') as image: # file path and name
                    # hashlib.md5(image_file).hexdigest()
                    img_hash = hashlib.md5(image.read()).hexdigest()
                    # time.strftime("%m/%d/%Y %I:%M:%S %p",time.localtime(os.path.getmtime(fname)))
                    # add anoterh try for regular date of os.path.getmtime(filepath)
                    try:
                        exif = exifread.process_file(image)
                        if (exif['EXIF DateTimeOriginal']):
                            dateobj = get_exif_date(str(exif['EXIF DateTimeOriginal']))
                            dates_array.append(dateobj)
                            #print("EXIF: " + str(dateobj))
                    except KeyError:
                        print("--> no EXIF data found")

                    try:
                        parser = createParser(targ)
                        metadata = extractMetadata(parser)
                        if(metadata.get('creation_date')):
                            date = str(metadata.get('creation_date'))
                            dateobj = get_cdate_date(date)
                            dates_array.append(dateobj)
                            #print("CDATE FOUND: " + str(dateobj))
                    except KeyError:
                        print("--> KeyError- no VIDEO METADATA data found")
                        pass
                    except ValueError:
                        print("--> ValueError- no VIDEO METADATA data found")
                        pass
                    except AttributeError:
                        print("--> AttributeError- no VIDEO METADATA data found")
                        pass
                        
            # Once dates_array completed
            if targ.endswith(IMAGE_TYPES):            
                try_add_new_file(dates_array, targ, ext, img_hash)
                print("##############")

        print("ALL DONE")
        print ("HASH SET: " + str(hash_set))
        save_hash_set_log()


if __name__== "__main__":
    try_load_hash_set_log()
    if os.path.isfile(log_copied):
        os.remove(log_copied)
    if os.path.isfile(log_not_copied):
        os.remove(log_not_copied)
    main()    

