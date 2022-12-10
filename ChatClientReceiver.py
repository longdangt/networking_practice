import socket
import sys
import random
import time
import zlib
from queue import PriorityQueue


# python3 ChatClientReceiver.py -s date.cs.umass.edu -p 8888
arguments = sys.argv
print(arguments)

#start connection setup
serverName = str(arguments[2])
serverPort = int(arguments[4])
destination = (serverName, serverPort)
receiverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
receiverSocket.settimeout(0.5)

def sendCommand(cmd):
    receiverSocket.sendto(cmd.encode(), destination)
    try:
        receivedMessage, serverAddr = receiverSocket.recvfrom(1024)
    except:
        print("Message did not successfully send, trying again")
        sendCommand(cmd)
    else:
        try:
            recvm = receivedMessage.decode()
        except:
            print("failed to decode command return")
            sendCommand(cmd)
        else:
            print(recvm)
    return

def changeMode():
    sendCommand(".")

setName = "NAME LDangReceiver"
connectTo = "CONN LDangSender"

sendCommand(setName)
sendCommand(connectTo)
#sets to relay mode
#changeMode()

def receiveAndSend():
    message, sA = receiverSocket.recvfrom(2048)
    print(message)
    returnMessage = "Sender Received: " + message
    receiverSocket.sendto(returnMessage, destination)
    return
unconnected = True

def checksum(data):
    return str(zlib.adler32(data)).encode()

def restartConnection():
    receiverSocket.close()
    receiverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    receiverSocket.settimeout(0.5)
    sendCommand(setName)
    sendCommand(connectTo)
    return

fileFlag = False
receivedACKS = []
timeoutCount = 0
dataQ = PriorityQueue()
expectingACK = 0

while True:
    try:
        print("trying to receive...")
        message, sA = receiverSocket.recvfrom(2048)
    except:
        #does not allow me to stop connection
        #if timeoutCount == 10:
        #     break
        print("failed receiving")
        timeoutCount += 1
        #receiverSocket.close()
        #receiverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        #receiverSocket.settimeout(0.5)
        #sendCommand(setName)
        #sendCommand(connectTo)
        continue
    else:
        #print("processing received data")
        data = message.split(b'.:bruh:.')
        #print(data)
        #print(data)
        if len(data) == 3:
            ack, r_checksum, msg = data
            #print(r_checksum)
            #print(checksum(msg))
            #########################
            try: 
                #print("trying to decode ACK...")
                receivedACK = int(ack.decode())
                #receivedMSG = msg.decode()
                #print(receivedACK)
                #print(receivedMSG)
            except:
                print("exception")
                continue
            else:
                #print("passed exception")
                #print("receivedACK: " + str(receivedACK))
                if receivedACK == -1:
                    expectingACK = 0
                    fileFlag = True
                    try:
                        receivedMSG = msg.decode()
                    except:
                        print("failed to read file name")
                        continue
                    else:
                        outFile = open(receivedMSG, "wb")
                if msg == b"!!QUIT!!":
                    for i in range(10):
                        receiverSocket.sendto(str(-2).encode(), destination)
                    break
                if receivedACK != -1 and receivedACK not in receivedACKS and r_checksum == checksum(msg): # and receivedACK == expectingACK:
                    #print("writing: " + receivedMSG)
                    if fileFlag:
                        expectingACK += 1
                        receivedACKS.append(receivedACK)
                        elementQ = (receivedACK, msg)
                        #print(elementQ)
                        dataQ.put(elementQ)
                        #outFile.write(receivedMSG)
                        #print(receivedACK)
                    else:
                        expectingACK += 1
                        receivedACKS.append(receivedACK)
                        sys.stdout(msg)
                if r_checksum != checksum(msg):
                    #print("checksum errror")
                    continue
                #if r_checksum == checksum(msg) and receivedACK == expectingACK-1:
                print("sending ACK: " + str(receivedACK))
                receiverSocket.sendto(str(receivedACK).encode(), destination)

quit_success = False
quit_fail_count = 0
quitMessages = [".", "QUIT"]
while not quit_success:
    for msg in quitMessages:
        receiverSocket.sendto(msg.encode(), destination)
        try:
            returnMsg, sA = receiverSocket.recvfrom(2048)
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
if fileFlag:
    while not dataQ.empty():
        token = dataQ.get()[1]
        outFile.write(token)
    outFile.close()
    
receiverSocket.close()