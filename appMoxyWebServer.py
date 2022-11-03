from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import io
from flask import Flask, render_template, send_file, make_response, request
app = Flask(__name__)
import sqlite3
import threading
import time
import serial
from bitstring import BitArray
from bitarray import bitarray
import struct
import sqlite3 as lite
import sys
from datetime import datetime
import json
import queue
from threading import Thread, Lock
###########################################
q_smo2_1 = queue.Queue(4)
q_smo2_2 = queue.Queue(4)

conn=sqlite3.connect('./sensorsData.db', check_same_thread=False)
curs=conn.cursor()

#/dev/COM[number]  [number = 0 to ...] possibly for windows users
serialPort = serial.Serial(port="/dev/ttyUSB0", baudrate=115200, bytesize=8, timeout=0.1, stopbits=serial.STOPBITS_ONE)

serialString = ""

mask4 = BitArray('0x0F')
mask2 = BitArray('0x0C')

counter = 0
sensor_id = 0

time_sensor1 = 0
sid1 = 0
smo2_val_sensor1 = 0 
thb_val_sensor1 = 0

time_sensor2 = 0
sid2 = 0
smo2_val_sensor2 = 0 
thb_val_sensor2 = 0

rolling_average_smo2_1 = 0
rolling_average_smo2_2 = 0

lock = threading.Lock()
###########################################
def Decode_func(line):
    if len(line) < 19:
        return len(line)
    else:  
        a = BitArray(bytes=line, offset=0)
        return a
###########################################
def Detect_Sensor_ID(dec):
    start_pos = 8
    end_pos = start_pos + 8
    bit_str = BitArray(dec[start_pos:end_pos])
    dev1 = BitArray('0x31')
    dev2 = BitArray('0x32')
    
    if bit_str == dev1:
        print("Channel is:", bit_str , " sensor 1 data")
        return 1
    elif bit_str == dev2:
        print("Channel is:", bit_str , " sensor 2 data")
        return 2
    print("Channel is:", bit_str , " sensor NOT DETECTED")
    return 3
###########################################
def Get_nibbles_bits(number, dec):
    start_pos = (number - 1) * 8
    end_pos = start_pos + 8
    bit_str = BitArray(dec[start_pos:end_pos])
    return bit_str
###########################################
def Get_ready_nibble_for_calculation(dec, mask):
    nibble = BitArray('0x00000000')
    dec &= mask
    nibble.overwrite(dec, 24)
    #print("NNNNNNNNNNNN:",nibble)
    return nibble
###########################################
def Calculate_THb(nibble1, nibble2, nibble3):
    nibble1 = nibble1 << 8
    nibble2 = nibble2 << 4
    return nibble1.uint + nibble2.uint + nibble3.uint
###########################################
def Calculate_SmO2(nibble1, nibble2, nibble3):
    nibble1 = nibble1 << 6
    nibble2 = nibble2 << 2
    nibble3 = nibble3 >> 2
    return nibble1.uint + nibble2.uint + nibble3.uint
###########################################
def Execute(dec):
    b = BitArray(mask4)
    c = BitArray(mask2)
    nibble4 = Get_nibbles_bits(4,dec)
    nibble3 = Get_nibbles_bits(3,dec)
    nibble4 &= b
    nibble4 = nibble4 << 4
    nibble3 &= b
    page = nibble4.uint + nibble3.uint
    if page == 1:
        page1_THb_nibble1 = Get_ready_nibble_for_calculation(Get_nibbles_bits(13,dec), b)
        page1_THb_nibble2 = Get_ready_nibble_for_calculation(Get_nibbles_bits(12,dec), b)
        page1_THb_nibble3 = Get_ready_nibble_for_calculation(Get_nibbles_bits(11,dec), b)
        THb = Calculate_THb(page1_THb_nibble1 , page1_THb_nibble2 , page1_THb_nibble3)
        print("THb:", THb * 0.01)
        page1_SmO2_nibble1 = Get_ready_nibble_for_calculation(Get_nibbles_bits(18,dec), b)
        page1_SmO2_nibble2 = Get_ready_nibble_for_calculation(Get_nibbles_bits(17,dec), b)
        page1_SmO2_nibble3 = Get_ready_nibble_for_calculation(Get_nibbles_bits(16,dec), c)
        SmO2 = Calculate_SmO2(page1_SmO2_nibble1 , page1_SmO2_nibble2 , page1_SmO2_nibble3)
        print("SmO2:", SmO2 * 0.1)
        SmO2 = SmO2 * 0.1
        THb = THb * 0.01
        return SmO2,THb
###########################################
def add_smo2_sensor1_to_QUEUE(sid, smo2_val, thb1_val):
    rolling_average = 0
    if q_smo2_1.full() == False:
        q_smo2_1.put(smo2_val)
    else:
        for i in range(0,4):
            rolling_average += q_smo2_1.queue[i]
        tmp_val = q_smo2_1.get()
        q_smo2_1.put(smo2_val)
        Insert_Data_To_DB(sid , rolling_average / q_smo2_1.qsize() , thb1_val)
    return rolling_average / q_smo2_1.qsize()
###########################################
def add_smo2_sensor2_to_QUEUE(sid, smo2_val, thb2_val):
    rolling_average = 0
    if q_smo2_2.full() == False:
        q_smo2_2.put(smo2_val)
    else:
        for i in range(0,4):
            rolling_average += q_smo2_2.queue[i]
        tmp_val = q_smo2_2.get()
        q_smo2_2.put(smo2_val)
        Insert_Data_To_DB(sid , rolling_average / q_smo2_2.qsize(), thb2_val)
    return rolling_average / q_smo2_2.qsize()
###########################################
def print_queue(queue_var):
    for i in range(0, queue_var.qsize()):
        print("Element ", i, " =", queue_var.queue[i])
###########################################
def Insert_Data_To_DB(sid , rolling_average_smo2 , val_thb):
    try:
        con = lite.connect('/home/pi/Desktop/test-final/sensorsData.db')
        print("Opened database...")
        cur = con.cursor()
        row = []
        row.append(str(datetime.now()))
        row.append(rolling_average_smo2)
        row.append(sid)
        row.append(val_thb)
        lock.acquire(True)
        cur.execute('INSERT INTO moxy_data VALUES (?, ?, ?, ?)', row)
        con.commit()
        print("Inserted......")
        cur.close()
    except lite.Error as error:
        print("Failed:" , error)
    finally:
        if con:
            con.close()
            lock.release()
            print("Connection closed111")
#################################################################################################
def Send_Serial_Command():#thread_safe):
    global controller
    global time_sensor1
    global sid1
    global smo2_val_sensor1 
    global thb_val_sensor1
    global time_sensor2
    global sid2
    global smo2_val_sensor2 
    global thb_val_sensor2
    global rolling_average_smo2_1
    global rolling_average_smo2_2

    while controller:
        # Wait until there is data waiting in the serial buffer
        if serialPort.in_waiting > 0:
            serialString = serialPort.readline()
            # Print the contents of the serial data
            try:
                print("acquired!!!!")
                dec = Decode_func(serialString)
                while len(serialString.decode()) < 19 or serialString.decode()[0] != '!' or not str(serialString.decode()[1]).isdigit():
                    serialString = serialPort.readline()
                    serialPort.flush()
                dec = Decode_func(serialString)
                sensor_id = Detect_Sensor_ID(dec)              
                while sensor_id == 3:
                    serialString = serialPort.readline()
                    serialPort.flush()
                    dec = Decode_func(serialString)
                    sensor_id = Detect_Sensor_ID(dec)
                tuple_val = Execute(dec)
                #This could be adjusted by user or removed as I did
                #time.sleep(2)             
                if not isinstance (tuple_val[0], type(None)) and sensor_id == 1:
                    now = datetime.now()
                    hours_minute = str(now.hour) + ":" + str(now.minute) + ":" + str(now.second)
                    time_sensor1 = str(hours_minute)
                    sid1 = sensor_id
                    smo2_val_sensor1 = tuple_val[0]
                    thb_val_sensor1 = tuple_val[1] 
                    rolling_average_smo2_1 = add_smo2_sensor1_to_QUEUE(sid1, smo2_val_sensor1, thb_val_sensor1)               
                    print_queue(q_smo2_1)
                    time.sleep(2)
                if not isinstance (tuple_val[0], type(None)) and sensor_id == 2:
                    now = datetime.now()
                    hours_minute = str(now.hour) + ":" + str(now.minute) + ":" + str(now.second)
                    time_sensor2 = str(hours_minute)
                    sid2 = sensor_id
                    smo2_val_sensor2 = tuple_val[0]
                    thb_val_sensor2 = tuple_val[1]
                    rolling_average_smo2_2 = add_smo2_sensor2_to_QUEUE(sid2, smo2_val_sensor2, thb_val_sensor2)
                    print_queue(q_smo2_2)
                    time.sleep(2)
                serialPort.flush()
            except Exception as e:
                print(e)

###Web server part of the code
#################################################################################################
@app.route("/")
def index():
    templateData = {}
    return render_template('index.html', **templateData)


@app.route("/livedata", methods=["GET", "POST"])
def plot_live_data():
    data = {}
    data['thb_1'] = thb_val_sensor1
    data['thb_2'] = thb_val_sensor2
    data['smo2_1'] = smo2_val_sensor1
    data['smo2_2'] = smo2_val_sensor2
    json_data = json.dumps(data)
    response = make_response(json.dumps(data))
    response.content_type = 'application/json'
    return response
###########################################
@app.route('/data', methods=["GET", "POST"])
def plot_smo2_sensor1():
    data = {}
    data['time_sensor1'] = time_sensor1
    data['smo2_1'] = rolling_average_smo2_1
    data['smo2_2'] = rolling_average_smo2_2
    json_data = json.dumps(data)
    response = make_response(json.dumps(data))
    response.content_type = 'application/json'
    return response
###########################################
if __name__ == "__main__":
    controller = 1
    serialPort.write("stop\r\n".encode())
    time.sleep(1)
    serialString = serialPort.readline()
    print(serialString.decode("Ascii"))
    serialPort.flush()
    time.sleep(1)
    serialPort.write("profile 1 1\r\n".encode())
    serialString = serialPort.readline()
    print(serialString.decode("Ascii"))
    serialPort.flush()
    serialString = serialPort.readline()
    print(serialString.decode("Ascii"))
    serialPort.flush()
    time.sleep(1)
    serialString = serialPort.readline()
    print(serialString.decode("Ascii"))
    serialPort.flush()
    time.sleep(1)
    #246 is one of the sensor ids. it could be adjusted by the user
    serialPort.write("sensor 1 246\r\n".encode())
    serialString = serialPort.readline()
    print(serialString.decode("Ascii"))
    serialPort.flush()
    time.sleep(1)
    serialString = serialPort.readline()
    print(serialString.decode("Ascii"))
    serialPort.flush()
    time.sleep(1)
    serialString = serialPort.readline()
    print(serialString.decode("Ascii"))
    serialPort.flush()
    time.sleep(1)
    print("-------END OF SENSOR 1 CONFIGURATION----------")
    serialPort.write("profile 2 1\r\n".encode())
    serialString = serialPort.readline()
    print(serialString.decode("Ascii"))
    serialPort.flush()
    serialString = serialPort.readline()
    print(serialString.decode("Ascii"))
    serialPort.flush()
    time.sleep(1)
    serialString = serialPort.readline()
    print(serialString.decode("Ascii"))
    serialPort.flush()
    time.sleep(1)
    #247 is one of the sensor ids. it could be adjusted by the user
    serialPort.write("sensor 2 247\r\n".encode())
    serialString = serialPort.readline()
    print(serialString.decode("Ascii"))
    serialPort.flush()
    time.sleep(1)
    serialString = serialPort.readline()
    print(serialString.decode("Ascii"))
    serialPort.flush()
    time.sleep(1)
    serialString = serialPort.readline()
    print(serialString.decode("Ascii"))
    serialPort.flush()
    time.sleep(1)
    serialString = serialPort.readline()
    print(serialString.decode("Ascii"))
    serialPort.flush()
    time.sleep(1)
    print("-------END OF SENSOR 2 CONFIGURATION----------")
    serialPort.write("start\r\n".encode())
    #time.sleep(1)
    serialString = serialPort.readline()
    print(serialString.decode("Ascii"))
    serialPort.flush()
    time.sleep(6)

    x = threading.Thread(target=Send_Serial_Command)

    x.start()
    app.run(host='0.0.0.0', port=80, debug=False)





