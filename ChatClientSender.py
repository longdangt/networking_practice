
import socket
import sys
import random
import time
import zlib
import re
from queue import PriorityQueue

# python3 ChatClientSender.py -s date.cs.umass.edu -p 8888
# python3 ChatClientSender.py -s date.cs.umass.edu -p 8888 -t testMessage.txt testOutput.txt

arguments = sys.argv
print(arguments)

serverName = str(arguments[2])
serverPort = int(arguments[4])
destination = (serverName, serverPort)
senderSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

if len(arguments) > 5:
    inputFile = str(arguments[6])
    outputFile = str(arguments[7])

senderSocket.settimeout(0.2)

states = ["COMMAND", "RELAY"]
currentState = states[0]

senderName = "NAME LDangSender"
senderSocket.sendto(senderName.encode(), destination)
initialMessage, serverAddr = senderSocket.recvfrom(2048)
print(initialMessage.decode())

connectCommand = "CONN LDangReceiver"
senderSocket.sendto(connectCommand.encode(), destination)
connectMessage, serverAddr = senderSocket.recvfrom(2048)
print(connectMessage.decode())

def checksum(data):
    return str(zlib.adler32(data)).encode()

def createMessage(ack, data):
    header = [str(ack).encode(), b'.:bruh:.', checksum(data), b'.:bruh:.']
    header.append(data)
    s_message = b''.join(header)
    return s_message

if len(arguments) == 5:
    readData = sys.stdin()
    data = [readData[i:i+1000] for i in range(0, len(readData), 1000)]
    #data.insert(0, outputFile.encode())
    #data.append(b"!!QUIT!!")
    #data.append(b"!!QUIT!!")
    #print(data)
    #print(len(data))
    #print(data[106])
    ack_n = 0
    for curMessage in data:
        #senderSocket.settimeout(10)
        fail_count = 0
        message = curMessage
        success = False
        quit_flag = False
        header = [str(ack_n).encode(), b'.:bruh:.', checksum(message), b'.:bruh:.']
        #print(header)
        header.append(message)
        s_message = b''.join(header)
        #print(s_message)
        while not success:
            print("sending: " + str(ack_n))
            senderSocket.sendto(s_message, destination)
            #if message == "QUIT":
            #    quit_flag = True
            #    break
            try:
                returnMsg, sA = senderSocket.recvfrom(2048)
                returnedACK = int(returnMsg.decode())
            except:
                if fail_count == 20:
                    break
                fail_count += 1
                print("Message not successfully sent, trying again")
            else:
                expectedACK = ack_n+1
                if expectedACK != returnedACK:
                    print("incorrect ack")
                    fail_count += 1
                    #if fail_count == 10:
                    #    break
                    continue
                else:
                    print("Received ACK: " + str(returnedACK))
                    ack_n += 1
                    success = True
        if quit_flag:
            break
else:
    iFile = open(inputFile, "rb")
    # https://www.pythonprogramming.in/how-to-split-a-byte-string-into-separate-bytes-in-python.html
    readData = iFile.read()
    data = [readData[i:i+1000] for i in range(0, len(readData), 1000)]
    dataQ = PriorityQueue()
    for i in range(len(data)):
        dataQ.put(i)
    windowSize = 10
    dataWindow = []
    completedACK = []
    #data.insert(0, outputFile.encode())

    sentFile = False
    while not sentFile:
        message = createMessage(-1, outputFile.encode())
        senderSocket.sendto(message, destination)
        try:
            returnMsg, sA = senderSocket.recvfrom(2048)
            returnedACK = int(returnMsg.decode())
        except:
            continue
        else:
            if returnedACK == -1:
                sentFile = True
    
    allComplete = False
    while not allComplete:
        #senderSocket.settimeout(10)
        print("Before ", dataWindow)
        while len(dataWindow) <= windowSize and not dataQ.empty():
            dataWindow.append(dataQ.get())
        print("After ", dataWindow)
        #header = [str(ack_n).encode(), b'.:bruh:.', checksum(message), b'.:bruh:.']
        #header.append(message)
        #s_message = b''.join(header)
        for i in dataWindow:
            s_message = createMessage(i, data[i])
            senderSocket.sendto(s_message, destination)
        for i in range(len(dataWindow)):
            try: 
                returnMsg, sA = senderSocket.recvfrom(2048)
                returnedACK = int(returnMsg.decode())
            except:
                print("Failed Receiving")
                continue
            else:
                print("Received ", returnedACK)
                if returnedACK in dataWindow and returnedACK not in completedACK:
                    completedACK.append(returnedACK)
                    dataWindow.remove(returnedACK)
        allComplete = len(data) == len(completedACK)

receiverNotQuit = False
receiverFailCount = 0
while not receiverNotQuit:
    quitM = createMessage(-2, b"!!QUIT!!")
    senderSocket.sendto(quitM, destination)
    try:
        returnMsg, sA = senderSocket.recvfrom(2048)
        returningACK = int(returnMsg.deocde())
    except:
        receiverFailCount += 1
        if receiverFailCount == 10:
            break
    else:
        if returnedACK == -2:
            break

quit_success = False
quit_fail_count = 0
quitMessages = [".", "QUIT"]
while not quit_success:
    for msg in quitMessages:
        senderSocket.sendto(msg.encode(), destination)
        try:
            returnMsg, sA = senderSocket.recvfrom(2048)
        except:
            quit_fail_count += 1
            if quit_fail_count == 10:
                break
            print("Quit Message not successfully sent, trying again")
        else:
            try:
                retMsg = returnMsg.decode()
            except:
                quit_fail_count += 1
                if quit_fail_count == 10:
                    break
                continue
            else:
                print(retMsg)
                if retMsg.split(" ")[0] == "OK":
                    quit_success = True
    


senderSocket.close()