import socket
import time
import argparse
from threading import Thread

def get_host_default_interface_ip():
    """ Xác định địa chỉ IP của máy """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 1))  # Kết nối đến Google DNS
        ip = s.getsockname()[0]    # Lấy địa chỉ IP của máy
    except Exception:
        ip = '127.0.0.1'           # Nếu lỗi, dùng localhost
    finally:
        s.close()
    return ip

def create_client_socket(host, port):
    """ Tạo client socket và kết nối đến server """
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))
    return client_socket  # Trả về socket để app.py dùng

def new_connection(tid, host, port):
    """ Kết nối client đến server và chạy phiên chat """
    print(f'Thread ID {tid} connecting to {host}:{port}')

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))

    chat_thread = Thread(target=chat_session, args=(client_socket))
    chat_thread.start()
    chat_thread.join()

    print(f'OK! I am ID={tid} done here')

def chat_session(client_socket):
    """ Phiên chat giữa client và server """
    try:
        while True:
            msg = input("Client: ")
            if msg.lower() == "exit":
                print("Đang đóng kết nối...")
                break
            client_socket.sendall(msg.encode())

            data = client_socket.recv(1024)
            if not data:
                break
            print(f"Server: {data.decode()}")
    except Exception as e:
        print(f"Lỗi: {e}")
    finally:
        client_socket.close()

def connect_server(threadnum, host, port):
    """ Tạo nhiều luồng để kết nối song song với server """
    threads = [Thread(target=new_connection, args=(i, host, port)) for i in range(threadnum)]
    [t.start() for t in threads]
    [t.join() for t in threads]

if __name__ == "__main__":
    host = get_host_default_interface_ip()  # Lấy IP tự động
    port = 22236  # Port cố định

    print(f"Đang kết nối đến server tại {host}:{port}...")
    connect_server(1, host, port)
