import socket
import sys
import random
import time
import threading

start = time.perf_counter()

arguments = sys.argv
fileName = str(arguments[1])
serverName = str(arguments[2])
serverPort = int(arguments[3])

sentence = "GET " + fileName + ".torrent\n"

# requests block
def block_request_msg(filename, blocknumber):
    message = "GET " + filename + ":" + str(blocknumber) + "\n"
    return message.encode()

# returns list of information from Torrent metadata reponse as a list:
# [num_blocks, file_size, [(ip, port)]]
def split_message(message):
    lines = message.split(b"\n")
    num_blocks = int(lines[0].split(b" ")[1])
    file_size = int(lines[1].split(b" ")[1])
    ip_p_list = []
    for i in range(2, len(lines)-1):
        if i%2 == 0:
            ip_adr = lines[i].split(b" ")[1].decode("utf-8")
            adr_port = int(lines[i+1].split(b" ")[1])
            ip_p_list.append((ip_adr, adr_port))
    return [num_blocks, file_size, ip_p_list]

#returns list of [code, body_offset, body_length]
def split_header(header):
    lines = header.split(b"\n")
    code = lines[0].decode("utf-8")
    body_offset = int(lines[1].split(b" ")[1])
    body_length = int(lines[2].split(b" ")[1])  
    return [code, body_offset, body_length]

# requests a block, writes puts it in dictionary of blocks
def request_blocks(filename, ip_port, total_blocks, first, last):
    #t_start = time.perf_counter()
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    clientSocket.connect(ip_port)
    for i in range(first, last):
        b_start = time.perf_counter()
        request_message = block_request_msg(filename, i)
        clientSocket.send(request_message)
        serverResponse = b""
        while True:
            serverResponse += clientSocket.recv(2048)
            if len(serverResponse) >= 2048:
                break
        header = serverResponse.split(b"\n\n")[0]
        body_offset = int(header.split(b"\n")[1].split(b" ")[1])
        body_length = int(header.split(b"\n")[2].split(b" ")[1])
        expectedLength = len(header) + 2 + body_length
        while True:
            serverResponse += clientSocket.recv(2048)
            if len(serverResponse) >= expectedLength:
                break
        body_bytes = serverResponse[len(header)+2:]
        blocks_data[i] = body_bytes
        print(len(blocks_data))
        b_end = time.perf_counter()
        print("Block time: " + str(b_end-b_start))
    #t_end = time.perf_counter()
    #print("Thread time: " + str(t_end-t_start))
    clientSocket.close()
    return


#start of server communication, gets torrent info
peers_list = []
def request_peers():
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    clientSocket.sendto(sentence.encode(),(serverName, serverPort))
    initialReturnMessage, serverAddress = clientSocket.recvfrom(2048)
    clientSocket.close()
    num_blocks, file_size, ip_p_list = split_message(initialReturnMessage)
    for peer in ip_p_list:
        peers_list.append(peer)
    print("Peers receieved!")
    return [num_blocks, file_size]

num_blocks, file_size = request_peers()


#time.sleep(2)
#for i in range(3):
#    time.sleep(1.5)
#    request_peers()

#request_peers()
#print(peers_list)
#print(file_size)
blocks_data = {}
ranges = []
for i in range(5):
    block = (num_blocks/5)*i
    ranges.append(int(block))
ranges.append(num_blocks)
threads = []
print("num_blocks: " + str(num_blocks))
print(ranges)

for i in range(len(ranges)-1):
    thread = threading.Thread(target= request_blocks, args= (fileName, peers_list[random.randint(0,len(peers_list)-1)], num_blocks, ranges[i], ranges[i+1]))
    thread.start()
    if i%2 == 1:
        time.sleep(2)
        request_peers()
    threads.append(thread)
#print(len(threads))
for thread in threads:
    thread.join()
#request_blocks(fileName, ip_p_list[0], num_blocks, 0, 10)

outputFile = open(fileName, "ab")
outputFile.truncate(0)
for i in range(num_blocks):
    outputFile.write(blocks_data[i])
outputFile.close()

end = time.perf_counter()
print(end-start)
# python3 P2PDownloader2.py redsox.jpg date.cs.umass.edu 19876