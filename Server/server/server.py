import socket
from threading import Thread
import login  # Nhúng login.py để kiểm tra tài khoản

def new_connection(addr, conn):
    """ Xử lý đăng nhập từ client, gửi phản hồi với định dạng code:<mã số>:<mã số> """
    try:
        data = conn.recv(1024).decode()
        print(f"Nhận từ {addr}: {data}")  # Debug: Kiểm tra dữ liệu nhận được

        if data.startswith("code:1:account:"):
            parts = data.split(":")
            if len(parts) == 6:
                username, password = parts[3], parts[5]
                result = login.verify_account(username, password)  # Kiểm tra tài khoản
                response = f"code:1:{result}"  # Định dạng phản hồi mới
                print(f"Gửi phản hồi cho {addr}: {response}")  # Debug: Kiểm tra phản hồi
                conn.sendall(response.encode())  # Gửi phản hồi về client

    except Exception as e:
        print(f"Lỗi xử lý client {addr}: {e}")

    finally:
        conn.close()

def get_host_default_interface_ip():
    """ Lấy địa chỉ IP của máy """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
       s.connect(('8.8.8.8',1))
       ip = s.getsockname()[0]
    except Exception:
       ip = '127.0.0.1'
    finally:
       s.close()
    return ip

def server_program(host, port):
    """ Server lắng nghe kết nối """
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serversocket.bind((host, port))
    serversocket.listen(10)
    print(f"Listening on {host}:{port}...")

    while True:
        conn, addr = serversocket.accept()
        nconn = Thread(target=new_connection, args=(addr, conn))
        nconn.start()

if __name__ == "__main__":
    hostip = get_host_default_interface_ip()
    port = 22236
    server_program(hostip, port)
