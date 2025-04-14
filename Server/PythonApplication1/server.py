import socket
import threading
import login  # Nhúng login.py để kiểm tra tài khoản
import register
import time

# --- Dữ liệu chia sẻ và Khóa ---
peers = {} # Dictionary lưu thông tin peer
# Key: tuple (ip, port_str) - Port là port mà peer lắng nghe, do peer gửi lên
# Value: dictionary {'username': '...', 'status': '...', 'ip': '...', 'port': '...','last_seen': timestamp}
peers_lock = threading.Lock() # Lock để bảo vệ truy cập vào 'peers'

# --- Hằng số ---
SERVER_PORT = 22236 # Port mặc định của Tracker
BUFFER_SIZE = 4096 # Kích thước bộ đệm nhận dữ liệu
PEER_TIMEOUT_SECONDS = 60 # Thời gian timeout cho peer không hoạt động (tùy chọn)

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

def new_connection(addr, conn):
    peer_ip = addr[0] # Đây sẽ là IP công cộng của peer (hoặc router của peer)
    peer_tracker_port = addr[1] # Port mà peer dùng để kết nối *đến* tracker
    peer_listen_key = None # Sẽ là tuple (ip, listening_port_str) của peer sau khi SUBMIT
    current_username = "Unknown" # Giữ lại để logging rõ hơn

    global tracker_socket, peer_list
    active_socket = None
    try:
        data = conn.recv(1024).decode().strip()
        print(f"Nhận từ {addr}: {data}")  # Debug: Kiểm tra dữ liệu nhận được
        if data.startswith("code:1:account:"):  # Xử lý đăng nhập
            parts = data.split(":")
            if len(parts) == 6:
                username, password = parts[3], parts[5]
                result = login.verify_account(username, password)  # Kiểm tra tài khoản
                response = f"code:1:{result}"
                print(f"Gửi phản hồi cho {addr}: {response}")  # Debug
                conn.sendall(response.encode())

        elif data.startswith("code:0:account:"):  # Xử lý đăng ký
            parts = data.split(":")
            if len(parts) == 6:
                username, password = parts[3], parts[5]

                result = register.register_account(username, password)  # Kiểm tra trùng tài khoản
                response = f"code:0:{result}"  # Đăng ký thành công
                print(f"Gửi phản hồi cho {addr}: {response}")  # Debug
                conn.sendall(response.encode())
                
        elif data.startswith == "SUBMIT:":
                # Định dạng: SUBMIT <listening_port> <username> <status>
             parts = data.split(":")
             if len(parts) == 4:
                listening_port_str = parts[1]
                username = parts[2]
                status = parts[3]
                # Key nên dùng IP mà tracker thấy (peer_ip) và port peer lắng nghe
                peer_listen_key = (peer_ip, listening_port_str)
                current_username = username # Cập nhật username

                with peers_lock:
                    peers[peer_listen_key] = {
                        'ip': peer_ip,             # IP công cộng của Peer (do tracker thấy)
                        'port': listening_port_str,# Port P2P Peer lắng nghe
                        'username': username,
                        'status': status,
                        'last_seen': time.time()
                    }
                # Log này nên rõ ràng IP lưu trữ là IP tracker thấy
                print(f"[Tracker] Peer '{username}' ({peer_ip}:{listening_port_str}) đã SUBMIT/cập nhật. IP '{peer_ip}' được lưu trữ.")
                try:
                    conn.sendall("SUBMIT_OK\n".encode('utf-8'))
                except socket.error as send_e:
                     print(f"[Tracker] Lỗi gửi SUBMIT_OK đến {addr}: {send_e}")
            # ... (Các lệnh khác như GETLIST, DISCONNECT giữ nguyên) ...

    except socket.error as e:
        print(f"[Tracker] Lỗi socket với {addr} ({current_username}): {e}")
    except Exception as e:
        print(f"[Tracker] Lỗi không xác định khi xử lý {addr} ({current_username}): {e}")
    finally:
        # --- Dọn dẹp khi kết nối kết thúc ---
        if peer_listen_key:
            with peers_lock:
                if peer_listen_key in peers:
                    removed_username = peers[peer_listen_key].get('username', 'unknown')
                    # Log rõ ràng key bị xóa
                    print(f"[Tracker] Xóa peer '{removed_username}' (key: {peer_listen_key}) khỏi danh sách do ngắt kết nối.")
                    del peers[peer_listen_key]

def server_program(host, port):
    """Khởi tạo và chạy vòng lặp chính của tracker server."""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        server_socket.bind((host, port))
        server_socket.listen(15)
        print(f"[Tracker] Server đang lắng nghe trên TẤT CẢ các giao diện ({host}) cổng {port}.")
        print(f"[Tracker] Các peer từ mạng ngoài cần kết nối đến ĐỊA CHỈ IP CÔNG CỘNG của mạng này và cổng {port} (đã được port forward).")

        while True:
            try:
                conn, addr = server_socket.accept()
                nconn = threading.Thread(target=new_connection, args=(addr, conn), name=f"Peer-{addr[0]}:{addr[1]}")
                nconn.daemon = True
                nconn.start()
            except Exception as e:
                print(f"[Tracker] Lỗi khi chấp nhận kết nối: {e}")

    except OSError as e:
         print(f"[Tracker] Lỗi khi bind server tới {host}:{port} - {e}. Cổng có thể đang được sử dụng hoặc không có quyền.")
    except KeyboardInterrupt:
         print("\n[Tracker] Server đang tắt do yêu cầu của người dùng (Ctrl+C).")
    except Exception as e:
        print(f"[Tracker] Lỗi nghiêm trọng của server: {e}")
    finally:
        print("[Tracker] Đang đóng socket server.")
        server_socket.close()

if __name__ == "__main__":
    host_ip = '0.0.0.0' # Luôn lắng nghe trên tất cả các giao diện
    server_port = SERVER_PORT

    # Lấy IP nội bộ CHỈ để hiển thị thông tin nếu cần, không dùng để bind
    try:
         display_ip = get_host_default_interface_ip()
         print(f"[Tracker] IP nội bộ có thể là: {display_ip} (chỉ để tham khảo, KHÔNG dùng để kết nối từ ngoài)")
    except Exception:
         print("[Tracker] Không thể lấy IP nội bộ để hiển thị.")

    server_program(host_ip, server_port)
