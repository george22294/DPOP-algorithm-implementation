import socket
import json


def send_udp_mes(type_of_mes, data, sendtoIP, sendtoPort):
    MESSAGE = json.dumps({"tp": type_of_mes, "dt": data})

    #sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(
        socket.SOL_SOCKET,
        socket.SO_SNDBUF,
        1000048576)
    sock.setsockopt(
        socket.SOL_SOCKET,
        socket.SO_RCVBUF,
        100048576)
    #bufsize = sock.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF)
    #print("Buffer size [Before]:%d" % bufsize)
    flagCon = False
    while not flagCon:


        try:

            sock.connect((sendtoIP, sendtoPort))
            sock.sendall(MESSAGE.encode())
            datarcv = sock.recv(100048576)
            #sock.sendto(MESSAGE.encode(), (sendtoIP, sendtoPort))
            flagCon = True

        except Exception as e:

            flagCon = False

        if flagCon:

            sock.close()


def receive_udp_mes(msgs, IP, Port):
    #sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(
        socket.SOL_SOCKET,
        socket.SO_SNDBUF,
        1000048576)
    sock.setsockopt(
        socket.SOL_SOCKET,
        socket.SO_RCVBUF,
        100048576)
    sock.bind((IP, Port))
    sock.listen()


    while True:
        #data, addr = sock.recvfrom(70048576)  # buffer size is 1024 bytes
        conn, addr = sock.accept()
        data = conn.recv(100048576)
        data_byte = data
        data = json.loads(data.decode())
        type_of_mes = data.get("tp")
        dt = data.get("dt")
        msgs[str(type_of_mes)] = dt
        conn.send(data_byte)