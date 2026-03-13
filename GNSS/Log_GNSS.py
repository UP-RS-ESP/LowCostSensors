# -*- coding: utf-8 -*-

import sys, os, glob
import serial
import datetime
import gzip

import psutil, time #Use this to check if the clock setting script is running. If so, wait to open serial port

def check_processes(script_name):
    running = True
    while running:
        for proc in psutil.process_iter():
            try:
                process_name = proc.name()
        
                # Check whether the process name matches the script name
                if process_name == "python" and script_name in proc.cmdline():
                    #running = True  # Process is still running
                    time.sleep(10)
                    break
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        else:
            running = False
        #time.sleep(10)
        
def read_compressed(save):
    with gzip.open(save, 'rt') as f:
        check = f.read()
    check = check.split('\n')
    return check

def flatten(l):
    """
    Flattens lists of lists into a single list.
    """
    try:
        return [item for sublist in l for item in sublist]
    except:
        return l
    
def compress_files(flist, output):
    flist.sort()
    full_file = []
    for f in flist:
        #print(f)
        data = read_compressed(f)
        full_file.append(data)
    
    full = flatten(full_file)
    write_compressed(full, output)

def time_from_gps(line):
    #Pull out the date to update current time
    data = line.split(',')
    date = data[9]
    tt = data[1]
    current_time = datetime.datetime(2000 + int(date[4:]), int(date[2:4]), int(date[:2]),\
                                     int(tt[:2]), int(tt[2:4]), int(tt[4:6]))

    return current_time
    
def write_output(output, save):
    with open(save + '.txt', 'w') as f:
        for l in output:
            f.write(l + '\n')
            
def write_compressed(output, save):
    with gzip.open(save, 'wt') as f:
        for l in output:
            f.write(l + '\n')
 
port_to_log, name, output_directory = sys.argv[1:]
if not os.path.exists(output_directory):
    os.mkdir(output_directory)
    
#Open serial device
if name == 'ADA_FEA':
    baud = 115200 #This is set in the arduino sketch! Sensor logs at 9600, but the M0 sends the data via L2C at 115200
else:
    baud = 9600
    
#Make sure the serial port is unblocked
check_processes('setPiClock.py')

while not datetime.datetime.utcnow() > datetime.datetime(1971,1,1):
    time.sleep(10) #Hang for wrong system time (wait on GPS time fix)
    
#Quick open/close serial port to make sure no one else is on it, also check alignment of signal
with serial.Serial(port=port_to_log, baudrate=baud, parity = serial.PARITY_NONE, stopbits = serial.STOPBITS_ONE, bytesize = serial.EIGHTBITS, timeout = 1) as ser:
    try:
        line = ser.readline().decode("utf-8").replace('\r', '').replace('\n', '') #read a line from serial port
    except:
        pass
    
#Start with empty data
current_time = None      
written = False
current_hour = -1

#Open connection to serial port
with serial.Serial(port=port_to_log, baudrate=baud) as ser:
    
    output = []
    while True:
        
        try:
            line = ser.readline().decode("utf-8").replace('\r', '').replace('\n', '') #read a line from serial port
            output.append(line)
            #print(line)
        except:
            pass

        #Get current time by looping through serial signal until GPS time is established
        if 'RMC' in line: #Time info
            try:
                current_time = time_from_gps(line)
            except:
                pass
            #if current_time.second % 30 == 0:
            if current_time.second == 0:
                print('Time', current_time.isoformat(), len(output))
        if not current_time:
            continue
        
        if current_time.minute in range(0,60,5):
            if current_time.second == 0:
                #output.append(datetime.datetime.utcnow().isoformat())
                if not written: #This is to catch the lines that occur at that min/sec! Several per RMC line...
                    hour_name = current_time.strftime('%Y-%m-%dT%H-%M') #Year, month, day, hour, min
                    
                    day_folder = output_directory + current_time.strftime('%Y-%m-%d')
                    if not os.path.exists(day_folder):
                        os.mkdir(day_folder)
                    raw_folder = day_folder + '/raw/'
                    if not os.path.exists(raw_folder):
                        os.mkdir(raw_folder)
                    
                    log_file = raw_folder + hour_name + '_' + name + '.txt.gz'
                    print('Dumping', len(output), 'lines to', log_file)
                    #Write output, clear the list
                    write_compressed(output, log_file)
                    output = []
                    written = True
            else:
                written = False
                
        #Squeeze down to hourly files for ease of transfer -- only when a full hour is done
        if not current_hour == current_time.hour and current_time.minute > 0: #Once an hour, compress last hours data
            #Top of every hour, compress to a single hourly zipped file
            prev_hour = datetime.datetime.utcnow() - datetime.timedelta(hours=1) #Handle over midnight
            hour_name = prev_hour.strftime('%Y-%m-%dT%H') #Year, month, day, hour
            comp_file = output_directory + prev_hour.strftime('%Y-%m-%d') + '/' + hour_name + '_' + name + '.txt.gz'
                
            if not os.path.exists(comp_file):
                flist = glob.glob(output_directory + prev_hour.strftime('%Y-%m-%d') + '/raw/' + hour_name + '-*_' + name + '.txt.gz')
                if len(flist) > 0:
                    print('Compressing', len(flist), 'files to', comp_file)
                    compress_files(flist, comp_file)
                    for f in flist:
                        os.remove(f)
                    #shutil.rmtree(output_directory + hour_name + '/raw/')
                else:
                    print('Nothing to compress in', output_directory + hour_name + '/raw/')
                current_hour = current_time.hour