import socket
import threading
import login  # Nhúng login.py để kiểm tra tài khoản
import register
import time
import channel
import json
import changestate
import chat
import sync
# --- Dữ liệu chia sẻ và Khóa ---
peers = {} # Dictionary lưu thông tin peer
# Key: tuple (ip, port_str) - Port là port mà peer lắng nghe, do peer gửi lên
# Value: dictionary {'username': '...', 'status': '...', 'ip': '...', 'port': '...','last_seen': timestamp}
peers_lock = threading.Lock() # Lock để bảo vệ truy cập vào 'peers'

# --- Hằng số ---
SERVER_PORT = 22236 # Port mặc định của Tracker
BUFFER_SIZE = 4096 # Kích thước bộ đệm nhận dữ liệu
PEER_TIMEOUT_SECONDS = 60 # Thời gian timeout cho peer không hoạt động (tùy chọn)
active_peers = []

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

def store_socket(conn, addr):
    global active_peers
    for i, (existing_conn, existing_addr) in enumerate(active_peers):
        if existing_addr[0] == addr[0]:  # Nếu IP đã tồn tại
            active_peers[i] = (conn, addr)  # Cập nhật socket & cổng
            return
    active_peers.append((conn, addr))
    
def remove_connection_by_addr(target_addr):
    """Xóa kết nối dựa trên địa chỉ IP & Port"""
    global active_peers  # Sử dụng danh sách toàn cục
    initial_count = len(active_peers)  # Số lượng peer trước khi xóa
    active_peers = [(conn, addr) for conn, addr in active_peers if addr != target_addr]

def new_connection(addr, conn):
    peer_ip = addr[0] # Đây sẽ là IP công cộng của peer (hoặc router của peer)
    peer_tracker_port = addr[1] # Port mà peer dùng để kết nối *đến* tracker
    peer_listen_key = None # Sẽ là tuple (ip, listening_port_str) của peer sau khi SUBMIT
    current_username = "Unknown" # Giữ lại để logging rõ hơn
    active_peers = []
    
    global tracker_socket, peer_list
    active_socket = None
    try:
        data = conn.recv(1024).decode().strip()
        print(f"Nhận từ {addr}: {data}")  # Debug: Kiểm tra dữ liệu nhận được
        if data.startswith("code:0:account:"):  # Xử lý đăng ký
            parts = data.split(":")
            if len(parts) == 6:
                username, password = parts[3], parts[5]
                ip, port = addr
                sync.update_connection(username,ip,port)
                result = register.register_account(username, password)  
                response = f"code:0:{result}"  
                print(f"Gửi phản hồi cho {addr}: {response}")  
                conn.sendall(response.encode())
                
        elif data.startswith("code:1:account:"):  
            parts = data.split(":")
            username, password = parts[3], parts[5]
            ip, port = addr
            sync.update_connection(username,ip,port)            
            result = login.verify_account(username, password) 
            channel_list = channel.get_user_channels(username)

            # Chuyển danh sách thành JSON
            channel_list_json = json.dumps(channel_list)
            response = f"code:1:{result}:{channel_list_json}"

            print(f"Gửi phản hồi cho {addr}: {response}")  
            conn.sendall(response.encode())

        elif data.startswith("code:2"):
            parts = data.split(":")
            channel_name = parts[4]
            username = parts[3]
            ip, port = addr
            sync.update_connection(username,ip,port)
            store_socket(conn, addr)
            result = channel.get_channel_members(channel_name)
            chat_data = chat.get_channel_chat(channel_name)
            response = f"code|2|{result}|{chat_data}"  
            print(f"Gửi phản hồi cho {addr}: {response}") 
            conn.sendall(response.encode())
                
        elif data.startswith("code:3"):
            parts = data.split(":")
            username = parts[2]
            ip, port = addr
            sync.update_connection(username,ip,port) 
            active_peers.append((conn, addr))
            state = parts[3]
            if state == "invisible":
                state = "offline"
                store_socket(conn, addr)
            if state == "offline":
                remove_connection_by_addr(addr)
            changestate.update_user_status(username,state)

        elif data.startswith("code:4"):
            parts = data.split(":")
            username = parts[2]
            ip, port = addr
            sync.update_connection(username,ip,port)
            store_socket(conn, addr)
            channel_name = parts[3]
            result = channel.join_channel_on_server(username,channel_name)
            response = f"code:4:{result}"
            conn.sendall(response.encode())
            print(f"Gửi phản hồi cho {addr}: {response}")  # Debug
            
            
        elif data.startswith("code:5"):
            parts = data.split(":")
            username = parts[2]
            ip, port = addr
            sync.update_connection(username,ip,port)
            store_socket(conn, addr)
            channel_list = channel.get_user_channels(username)
            channel_list_json = json.dumps(channel_list)
            response = f"code:5:{channel_list_json}"
            conn.sendall(response.encode())  
            print(f"Gửi phản hồi cho {addr}: {response}")  # Debug
               
            
        elif data.startswith("code:6"):
            parts = data.split(":")
            username = parts[2]
            channel_name = parts[3]
            ip, port = addr
            sync.update_connection(username,ip,port)
            store_socket(conn, addr)
            result = channel.add_channel(username,channel_name)
            chat.create_chat_file(channel_name)
            response = f"code:6:{result}"
            conn.sendall(response.encode())       
            print(f"Gửi phản hồi cho {addr}: {response}")  # Debug
    
        elif data.startswith("code:7"):
            count = 0  # Đếm số lần gặp `:`
            index = -1  # Vị trí của dấu `:` thứ 3
            for i, char in enumerate(data):  # Duyệt từng ký tự trong chuỗi
                if char == ":":
                    count += 1
                    if count == 3:  # Nếu là dấu `:` thứ 3
                        index = i
                        break  # Thoát vòng lặp khi tìm thấy
                    
            prefix_data = data[:index]
            remaining_data = data[index+1:]
            parts = prefix_data.split(":")
            username = parts[2]  # Lấy tên người gửi
            ip, port = addr
            sync.update_connection(username,ip,port)
            store_socket(conn, addr)
            remaining_data = remaining_data.replace("'", "\"") 
            message_list = json.loads(remaining_data)    
            channel_name_to_send = ""
            for message in message_list:
                channel_name = message["channel"]  # Lấy tên kênh từ tin nhắn đầu tiên
                channel_name_to_send = channel_name
                content = message["content"]  # Lấy nội dung tin nhắn
                chat.process_received_message(username, channel_name, content)
            chat_data = chat.get_channel_chat(channel_name_to_send)
            response = f"code|7|{chat_data}"     
            conn.sendall(response.encode()) 
            
                
            
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
