import serial
import time
import keyboard
from bitstring import BitArray
from bitarray import bitarray
import struct
import sqlite3 as lite
import sys

serialPort = serial.Serial(port="COM8", baudrate=115200, bytesize=8, timeout=0.1, stopbits=serial.STOPBITS_ONE)

serialString = ""

mask4 = BitArray('0x0F')
mask2 = BitArray('0x0C')

#con = lite.connect('/home/pi/Desktop/Sensors_Database/sensorsData.db')
#cur = con.cursor()

sensor_id = 0

def Insert_Data_To_DB(sid , val_smo2 , val_thb):
    print("DATA..................", val_smo2, type(val_smo2), " - " , val_thb , type(val_thb) , counter)
    #if type(val) == NoneType:
    #    print("VVVVVVVVVVV:", val)
    #    val = 0
    #    print("now val:", val)
    #else:
    #    print("NISSSSSSSSSSSSSt", type(val))

    try:
        con = lite.connect('/home/pi/Desktop/Sensors_Database/sensorsData.db')
        print("Opened database...")
        cur = con.cursor()
        #insert_query = INSERT INTO moxy_data (timestamp, val) VALUES (?, ?);
        #data_tuple = (str(datetime.now(), val)
        #cur.execute(insert_query, data_tuple)
        row = []
        row.append(str(datetime.now()))
        row.append(val_smo2)
        row.append(sid)
        row.append(val_thb)
        cur.execute('INSERT INTO moxy_data VALUES (?, ?, ?, ?)', row)
        con.commit()
        print("Inserted......")
        cur.close()
        #displayData()
    except lite.Error as error:
        print("Failed:" , error)
    finally:
        if con:
            con.close()
            print("Connection closed111")


def displayData():
    print("Displaying.....")
    try:
        con = lite.connect('/home/pi/Desktop/Sensors_Database/sensorsData.db')
        curs = con.cursor()
        print ("\nEntire database contents:\n")
        for row in curs.execute("SELECT * FROM moxy_data"):
            print (row)
        curs.close()
    except lite.Error as error:
        print("Failed:" , error)
    finally:
        if con:
            con.close()
            print("Connection closed")





def Decode_func(line):
    if len(line) < 19:
        return
    else:  
        a = BitArray(bytes=line, offset=0)
        return a

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
    return 0


def Get_nibbles_bits(number, dec):
    start_pos = (number - 1) * 8
    end_pos = start_pos + 8
    bit_str = BitArray(dec[start_pos:end_pos])
    return bit_str

def Get_ready_nibble_for_calculation(dec, mask):
    nibble = BitArray('0x00000000')
    dec &= mask
    nibble.overwrite(dec, 24)
    #print("NNNNNNNNNNNN:",nibble)
    return nibble

def Calculate_THb(nibble1, nibble2, nibble3):
    nibble1 = nibble1 << 8
    nibble2 = nibble2 << 4
    return nibble1.uint + nibble2.uint + nibble3.uint


def Calculate_SmO2(nibble1, nibble2, nibble3):
    nibble1 = nibble1 << 6
    nibble2 = nibble2 << 2
    nibble3 = nibble3 >> 2
    return nibble1.uint + nibble2.uint + nibble3.uint
###########################################
def Execute(dec):
    print("Calculate_MO2:")
    
    b = BitArray(mask4)
    c = BitArray(mask2)
    nibble4 = Get_nibbles_bits(4,dec)
    nibble3 = Get_nibbles_bits(3,dec)
    nibble4 &= b
    nibble4 = nibble4 << 4
    nibble3 &= b
    page = nibble4.uint + nibble3.uint
    print("page is:" , page)
    print("==========================================")
    if page == 1:

        print("Thb Reading ....")
        page1_THb_nibble1 = Get_ready_nibble_for_calculation(Get_nibbles_bits(13,dec), b)
        page1_THb_nibble2 = Get_ready_nibble_for_calculation(Get_nibbles_bits(12,dec), b)
        page1_THb_nibble3 = Get_ready_nibble_for_calculation(Get_nibbles_bits(11,dec), b)
        THb = Calculate_THb(page1_THb_nibble1 , page1_THb_nibble2 , page1_THb_nibble3)
        #print("CLACCCCCCCCCCCCCCCCCCCCCCC:", myVal)
        print("THb:", THb * 0.01)
        print("###################################################")
        print("SmO2 Reading ....")
        page1_SmO2_nibble1 = Get_ready_nibble_for_calculation(Get_nibbles_bits(18,dec), b)
        page1_SmO2_nibble2 = Get_ready_nibble_for_calculation(Get_nibbles_bits(17,dec), b)
        page1_SmO2_nibble3 = Get_ready_nibble_for_calculation(Get_nibbles_bits(16,dec), c)
        SmO2 = Calculate_SmO2(page1_SmO2_nibble1 , page1_SmO2_nibble2 , page1_SmO2_nibble3)
        print("SmO2:", SmO2 * 0.1)
        SmO2 = SmO2 * 0.1
        THb = THb * 0.01
        return SmO2,THb
        
    



def Send_Serial_Command(command):

    if command == "start\r\n":
        serialPort.write(command.encode())
        while 1:
            # Wait until there is data waiting in the serial buffer
            if serialPort.in_waiting > 0:

                if keyboard.is_pressed('q'):
                    command = "stop\r\n"
                    serialPort.write(command.encode())
                    time.sleep(0.5)
                    serialString = serialPort.readline()
                    print(serialString)
                    serialPort.flush()
                    time.sleep(0.5)
                    print("Amir----Stopped")
                    
                # Read data out of the buffer until a carraige return / new line is found
                serialString = serialPort.readline()

                

                # Print the contents of the serial data
                try:
                    dec = Decode_func(serialString)
                    sensor_id = Detect_Sensor_ID(dec)
                    tuple_val = Execute(dec)
                    if not isinstance (tuple_val[0], type(None)):
                        print("ttt")
                        #Insert_Data_To_DB(sensor_id , tuple_val[0], tuple_val[1])
                    
                    #displayData()
                    serialPort.flush()
                    time.sleep(0.5)
                    #print(serialString.decode("Ascii"))
                except:
                    pass
    else:
        serialPort.write(command.encode())
        time.sleep(0.5)
        serialString = serialPort.readline()
        print(serialString.decode("Ascii"))
        serialPort.flush()
        time.sleep(0.5)
        print("---------------------")

Send_Serial_Command("stop")
Send_Serial_Command("\r\n")
Send_Serial_Command("profile 1 1\r\n")
Send_Serial_Command("sensor 1 247\r\n")
#Send_Serial_Command("start\r\n")


#Send_Serial_Command("stop")
Send_Serial_Command("\r\n")
Send_Serial_Command("profile 2 1\r\n")
Send_Serial_Command("sensor 2 246\r\n")
Send_Serial_Command("start\r\n")

