import base64
import binascii



# Pass in the attaching string, the function attaches it after the SMMP header,
# returns the bytes form of the final string.
# As the SNMP header only have 1 byte of length field,
# the maximum length of the attach string is 255 - 27 = 228.
def GenPacket(attach):

    length = 27 + len(attach) // 2
    length = hex(length)
    length = length[2 : ]

    header = ""

    header += "30"                         # The next byte is a length var
    header += length                       # The length of the message starting form the next byte 
    header += "020100"                     # SNMP Version Number, SNMPv1, using BER encoding rules
    header += "04067075626C6963"           # Comunity string ASCII "70...63" => "public"
    header += "A1"                         # PUD type "get-next-request"
    

    hexstr = str(hex(int(length,16)-13))
    hexstr = hexstr[2 : ]                  # Remove the "0x"
    if len(hexstr) == 1:
        hexstr = "0" + hexstr
    header += hexstr

    header += "020422708BD4"               # Request ID
    header += "020100"                     # Error state = 0, BER
    header += "020100"                     # Error index = 0, BER
    header += "30"                         # The next byte is a length var
    
    hexstr = str(hex(int(length,16)-27))
    hexstr = hexstr[2 : ]                  # Remove the "0x"    
    if len(hexstr) == 1:
        hexstr = "0" + hexstr
    elif len(hexstr) == 0:
        hexstr = "00"
    header += hexstr

    # End at the "key-value pair" length
    # It's in the PDU part  
    
    return base64.b16decode(header + attach, True)  # Using it as "hex to raw" dumper

