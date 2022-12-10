
from ast import arg
from email.iterators import body_line_iterator
#from socket import *
import socket
import sys
import argparse

arguments = sys.argv

fileName = str(arguments[1])
serverName = str(arguments[2])
serverPort = int(arguments[3])
clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
clientSocket.connect((serverName,serverPort))

sentence = "GET " + fileName + "\n"
clientSocket.send(sentence.encode())
serverResponse = clientSocket.recv(1024)
header = serverResponse.split(b"\n\n")[0]
body_offset = int(header.split(b"\n")[1].split(b" ")[1])
body_length = int(header.split(b"\n")[2].split(b" ")[1])
totalMessageLength = len(header) + 2 + body_offset + body_length

totalMessage = serverResponse
while True:
    totalMessage += clientSocket.recv(1024)
    if len(totalMessage) >= totalMessageLength:
        break

bodyMessage = totalMessage[len(header)+2:]
outputFile = open(fileName, "wb")
outputFile.write(bodyMessage)
outputFile.close()

clientSocket.close()

# python3 CSDownloader.py test.jpg pear.cs.umass.edu 18765