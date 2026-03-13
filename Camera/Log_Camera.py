# -*- coding: utf-8 -*-

import sys, os, traceback, time
import datetime
import numpy as np
from PIL import Image

from picamera import PiCamera
import picamera.array as pcarray

name, output_directory = sys.argv[1:]
if not os.path.exists(output_directory):
    os.mkdir(output_directory)

lr = [960, 540]
hr = [3280, 2464] #3280 x 2464 max!
video_length = 10

def get_video(xres, yres, video_length, fname):
    #Typically, HD resolution (1,920 × 1,080 @ 30 fps)
    #allows to obtain satisfying results, as most visible but short lived
    #surfaced structures persist for at least O(0.1)s
    #Via: https://www.frontiersin.org/articles/10.3389/frwa.2021.766918/full
    with PiCamera() as camera:
        time.sleep(5)
        camera.resolution = (xres, yres) #Full HD
        camera.led = False #Keep the light off
        camera.start_recording(fname, format='h264')
        camera.wait_recording(video_length)
        camera.stop_recording()
        time.sleep(5)
        
def get_still(xres, yres, fname):
    save = True
    with PiCamera() as camera:
        time.sleep(5)
        camera.resolution = (xres, yres) #Full HD
        camera.led = False #Keep the light off
        camera.start_preview()
        time.sleep(5)
        camera.capture(fname)
        camera.stop_preview()
        time.sleep(5)
    arr = Image.open(fname) #Open and delete to dark images so they don't get shipped
    if np.nanmean(arr) < 10:
        os.remove(fname)
        save = False
        
    return save

while not datetime.datetime.utcnow() > datetime.datetime(1971,1,1):
    time.sleep(10) #Hang for wrong system time (wait on GPS time fix)

while True:
    #Rely on internal date
    current_time = datetime.datetime.utcnow()
    day_folder = output_directory + current_time.strftime('%Y-%m-%d') + '/'
    if not os.path.exists(day_folder):
        os.mkdir(day_folder)
        
    # if current_time.minute in range(0,60,5): #Every 5 mins
    #     hour_name = current_time.strftime('%Y-%m-%dT%H-%M') #Year, month, day, hour, min
    #     log_file = day_folder + hour_name + '_' + name
    #     if not os.path.exists(log_file + '_lr.jpg'):
    #         print('Logging LR', log_file + '_lr.jpg')
    #         try:
    #             save = get_still(lr[0], lr[1], log_file + '_lr.jpg')
    #         except:
    #             traceback.print_exc()
    #             save = False
                
    if current_time.minute in range(0,60,20): #Every 20 mins
        hour_name = current_time.strftime('%Y-%m-%dT%H-%M') #Year, month, day, hour, min
        log_file = day_folder + hour_name + '_' + name
        if not os.path.exists(log_file + '_hr.jpg'):
            print('Logging HR', log_file + '_hr.jpg')
            try:
                save = get_still(hr[0], hr[1], log_file + '_hr.jpg')
            except:
                traceback.print_exc()
                save = False
            if save:
                if current_time.minute == 0: #Log video data once an hour
                    if not os.path.exists(log_file + f'_{video_length}s.h264'):
                        print('Logging Video', log_file + f'_{video_length}s.h264')
                        try:
                            vidx, vidy = 1920, 1080
                            get_video(vidx, vidy, video_length, log_file  + f'_{video_length}s.h264')
                        except:
                            #Put this traceback in a log file
                            traceback.print_exc()     
    else:
        time.sleep(25) #Sleep to save CPU cycling