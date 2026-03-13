# -*- coding: utf-8 -*-

import sys, os, traceback, time
import serial
import datetime
import gzip
import numpy as np
#import matplotlib.pyplot as plt

baud = 115200
   
def log_data(line, fname):
    arr = transform_line(line)
    
    with gzip.GzipFile(fname, 'w') as f:
        np.save(f, arr)
        
def save_data(arr, fname):
    with gzip.GzipFile(fname, 'w') as f:
        np.save(f, arr)
        
def transform_line(line):
    arr = np.array(line.split(',')[:-1]).astype(float)
    arr = arr.reshape([24,32])
    return arr
        
def load_data(fname):
    with gzip.GzipFile(fname, 'r') as f:
        arr = np.load(f)
    return arr

def plot_line(line, fname):
    plt.close('all')
    f, ax = plt.subplots(1, figsize=(10,10))
    arr = np.array(line.split(',')[:-1]).astype(float)
    arr = arr.reshape([24,32])
    a = ax.imshow(arr, vmin=15, vmax=35, cmap='coolwarm')
    plt.colorbar(a)
    f.savefig(fname)
    plt.close('all')
    
port_to_log, name, output_directory = sys.argv[1:]

if not os.path.exists(output_directory):
    os.mkdir(output_directory)
    
while not datetime.datetime.utcnow() > datetime.datetime(1971,1,1):
    time.sleep(10) #Hang for wrong system time (wait on GPS time fix)
    
current_minute = -1
datalist = []
while True:
    #Rely on internal date
    current_time = datetime.datetime.utcnow()
    day_folder = output_directory + current_time.strftime('%Y-%m-%d') +'/'
    if not os.path.exists(day_folder):
        os.mkdir(day_folder)
        
    try:
        with serial.Serial(port=port_to_log, baudrate=baud, timeout = 2) as ser:
            time.sleep(1)
            line = ser.readline().decode("utf-8").replace('\r', '').replace('\n', '') #read a line from serial port
            single_arr = transform_line(line)
            datalist.append(single_arr)
            print('Line added...')
            False
    except:
        pass
        
    if not current_time.minute == current_minute:
        if current_time.minute % 5 == 0: #Only log every 5 mins
            n = len(datalist)
            hour_name = current_time.strftime('%Y-%m-%dT%H-%M') #Year, month, day, hour, min
            log_file = day_folder + hour_name + '_' + name
    
            data = np.dstack(datalist)
            mn = np.nanmean(data, 2)
            std = np.nanstd(data, 2)
            med = np.nanmedian(data, 2)
            save_data(mn, log_file + '_n=' + str(n) + '_mn.npy.gz')
            save_data(std, log_file + '_n=' + str(n) + '_std.npy.gz')
            save_data(med, log_file + '_n=' + str(n) + '_med.npy.gz')
            
            print('Data Logged...', log_file)
            datalist = []
            
        current_minute = current_time.minute