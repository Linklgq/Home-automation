import socket
import struct

def SetConn(host):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.connect(host)
    return sock

def main():
    host = ("127.0.0.1", 12580)
    sock = SetConn(host)

    while True:
        bufSize = struct.unpack("i", sock.recv(4))[0]
        print("Receive %d bytes"%bufSize)

        buf = b""
        while bufSize > 0:
            tempBuf = sock.recv(bufSize)
            buf += tempBuf
            bufSize -= len(tempBuf)

        sock.send(struct.pack("i", len(buf)) + buf)

if __name__ == "__main__":
    main()
