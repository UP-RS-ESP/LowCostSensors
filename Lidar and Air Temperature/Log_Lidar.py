# -*- coding: utf-8 -*-

import sys, os, time, traceback
import serial
import datetime
import gzip
import numpy as np
    
def build_average(dates, dists, temps, intensities, nrs):
    mn_dist = np.nanmean(dists)
    std_dist = np.nanstd(dists)
    p25_dist = np.nanpercentile(dists,25)
    p75_dist = np.nanpercentile(dists,75)
    med_dist = np.nanmedian(dists)
    mn_temp = np.nanmean(temps)
    std_temp = np.nanstd(temps)
    
    mn_int = np.nanmean(temps)
    std_int = np.nanstd(temps)
    
    n = np.nansum(nrs) #Each measurement of dist and power is an aggregate (10 shots per second) which is what is read from the arduino code
    
    d = dates[-1].isoformat()
    return d, str(mn_dist), str(std_dist), str(mn_temp), str(std_temp), str(len(dists)), str(p25_dist), str(p75_dist), str(med_dist), str(mn_int), str(std_int), str(n)
            
def write_plain(output, save):
    with open(save + '_raw.csv', 'a') as f:
        f.write(','.join(output) + '\n')
        
def write_full(dates, dists, temps, cts, ints, save):
    with open(save + '_raw.csv', 'a') as f:
        for i in range(len(dates)):    
            f.write(','.join([dates[i].isoformat(),str(dists[i]),str(temps[i]),str(cts[i]),str(ints[i])]) + '\n')
        
def compress_file(in_file, out_file, header):
    with open(in_file, 'r') as f_in, gzip.open(out_file, 'wt') as f_out:
        f_out.write(header)
        f_out.writelines(f_in)
    
port_to_log, name, output_directory = sys.argv[1:]
if not os.path.exists(output_directory):
    os.mkdir(output_directory)
    
while not datetime.datetime.utcnow() > datetime.datetime(1971,1,1):
    time.sleep(10) #Hang for wrong system time (wait on GPS time fix)
    
#Open serial device
baud = 115200 #This is the default for 40m lidar, via Arduino code

dates, dists, temps, cts, ints = [], [], [], [], []

print('Logging...')
current_minute = -1
current_hour = -1
#Open connection to serial port
with serial.Serial(port=port_to_log, baudrate=baud) as ser:    
    while True:
        #Rely on internal date
        current_time = datetime.datetime.utcnow()
        day_folder = output_directory + current_time.strftime('%Y-%m-%d') + '/'
        if not os.path.exists(day_folder):
            os.mkdir(day_folder)
        
        try:
            line = ser.readline().decode("utf-8").replace('\r', '').replace('\n', '') #read a line from serial port
            print(line)
            dates.append(current_time)
            nr = line.split(',')[0].split(':')[1].replace(' ','')
            dist = line.split(',')[1].split(':')[1].replace(' ','').replace('mm', '')
            sigstr = line.split(',')[2].split(':')[1].replace(' ','')
            temp = line.split(',')[3].split(':')[1].replace(' ','')

            dists.append(float(dist))
            temps.append(float(temp))
            cts.append(float(nr))
            ints.append(float(sigstr))
            print(line)
            
        except:
            traceback.print_exc()
            #pass
        
        if not current_time.minute == current_minute:
            #Build the minute average
            minute_data = build_average(dates, dists, temps, ints, cts)
            
            #Write that line to an uncompressed file to store up for an hour, then compress at the end
            hour_name = current_time.strftime('%Y-%m-%dT%H') #Year, month, day, hour
            log_file = day_folder + hour_name + '_' + name
            log_file_full = day_folder + hour_name + '_' + name + '_full'
            
            #if current_time.minute in [0, 15, 30, 45]:
            #    print('Writing raw data...', len(dates))
            #    print('Mean Dist:', np.nanmean(dists), 'STD:', np.nanstd(dists))
                
            write_plain(minute_data, log_file)
            write_full(dates, dists, temps, cts, ints, log_file_full)
            print('Line Written...')
            dates, dists, temps, cts, ints = [], [], [], [], []
            current_minute = current_time.minute
                
        if not current_hour == current_time.hour: #Once an hour, compress last hours data
            #Top of every hour, compress the plain text to a single hourly zipped file
            prev_hour = datetime.datetime.utcnow() - datetime.timedelta(hours=1) #Handle over midnight
            hour_name = prev_hour.strftime('%Y-%m-%dT%H') #Year, month, day, hour
            comp_file = output_directory + prev_hour.strftime('%Y-%m-%d') + '/' + hour_name + '_' + name

            if os.path.exists(comp_file + '_raw.csv'):
                print('Compressing', comp_file)
                compress_file(comp_file + '_raw.csv', comp_file + '.csv.gz', 'date,dist,dist_std,temp,temp_std,nr_meas,p25_dist,p75_dist,med_dist,mean_str,std_str,nr_raw_meas\n')
                os.remove(comp_file + '_raw.csv')
                
            if os.path.exists(comp_file + '_full_raw.csv'):
                print('Compressing', comp_file, 'Full Res')
                compress_file(comp_file + '_full_raw.csv', comp_file + '_full.csv.gz', 'date,dist,temp,raw_ct,sig_str\n')
                os.remove(comp_file + '_full_raw.csv')
           
            current_hour = current_time.hour
