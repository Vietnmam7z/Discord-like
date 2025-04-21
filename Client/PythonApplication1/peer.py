# -*- coding: utf-8 -*-
import socket
import threading
import json
import time
import argparse
import sys
import queue
import client
import GUI
# --- Globals & Shared State ---
my_username = "DefaultUser"
my_status = "online"
my_listen_port = 0
my_ip = "" # Sẽ được lấy tự động
client_socket = None
tracker_connected = threading.Event() # Dùng để báo hiệu kết nối tracker thành công
peer_server_socket = None
peer_list = [] # Danh sách các peer khác [{ 'ip': ..., 'port': ..., ...}, ...]
peer_list_lock = threading.Lock() # Bảo vệ truy cập peer_list
command_queue = queue.Queue() # Hàng đợi lệnh gửi đến tracker
exit_flag = threading.Event() # Cờ báo hiệu chương trình nên thoát
current_channel_id = "general" # Kênh chat mặc định
print_lock = threading.Lock() # Lock để tránh print bị chồng chéo từ các luồng

# --- Constants ---
BUFFER_SIZE = 4096
P2P_CONNECT_TIMEOUT = 3.0 # Timeout khi kết nối đến peer khác (giây)

def safe_print(message):
    # Phiên bản safe_print đơn giản nhất, chỉ print
    with print_lock:
        print(message)
        sys.stdout.flush()

# --- Peer Server Role (Listening for other peers) ---
def handle_incoming_peer_connection(peer_conn, peer_addr):
    """Xử lý kết nối đến từ một peer khác."""
    safe_print(f"[PeerServer] Có kết nối P2P từ {peer_addr}")
    peer_info_str = f"{peer_addr[0]}:{peer_addr[1]}"
    try:
        while not exit_flag.is_set():
            try:
                peer_conn.settimeout(1.0)
                data = peer_conn.recv(BUFFER_SIZE)
                if not data:
                    safe_print(f"[PeerServer] Peer {peer_info_str} đã ngắt kết nối P2P.")
                    break
            except socket.timeout:
                continue
            except ConnectionResetError:
                 safe_print(f"[PeerServer] Kết nối P2P bị reset bởi {peer_info_str}")
                 break
            except Exception as e:
                safe_print(f"[PeerServer] Lỗi nhận P2P từ {peer_info_str}: {e}")
                break

            message = data.decode('utf-8').strip()

            parts = message.split(' ', 3)
            p2p_command = parts[0].upper()

            # --- Xử lý lệnh MSG cơ bản ---
            if p2p_command == "MSG" and len(parts) == 4:
                channel = parts[1]
                sender = parts[2]
                content = parts[3]
                safe_print(f"[#{channel} | {sender}]: {content}")
            else:
                safe_print(f"[PeerServer] Nhận lệnh P2P không rõ từ {peer_info_str}: {message}")

    except socket.error as e:
        safe_print(f"[PeerServer] Lỗi socket P2P với {peer_info_str}: {e}")
    except Exception as e:
        safe_print(f"[PeerServer] Lỗi xử lý P2P với {peer_info_str}: {e}")
    finally:
        safe_print(f"[PeerServer] Đóng kết nối P2P với {peer_info_str}")
        peer_conn.close()

# --- Tracker Client Role ---
def tracker_handler(tracker_ip, tracker_port):
    """Luồng xử lý kết nối và giao tiếp với Tracker."""
    global tracker_socket, peer_list, my_listen_port, my_username, my_status
    try:
        print(f"[TrackerClient] Đang kết nối đến Tracker {tracker_ip}:{tracker_port}...") # Dùng print thường
        active_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        active_socket.settimeout(10.0)
        active_socket.connect((tracker_ip, tracker_port))
        active_socket.settimeout(None)
        tracker_socket = active_socket
        print("[TrackerClient] Đã kết nối Tracker.") # Dùng print thường
        tracker_connected.set()
    finally:
        if not tracker_connected.is_set():
            print("[TrackerClient] Kết nối không thành công.")

# --- P2P Message Sending ---
def send_p2p_message(message):
    submit_command = f"code:2:{my_listen_port}:{my_username}:{message}"
    client_socket.sendall(submit_command.encode())
    print(f"Đã gửi lệnh: {submit_command}")

def reconnect(username, status="online"):
    global my_username, my_status, my_listen_port, my_ip, client_socket
    tracker_ip = client.get_host_default_interface_ip()  
    tracker_port = 22236
    client_socket = client.create_client_socket(tracker_ip, tracker_port)
    tracker_thread = threading.Thread(target=tracker_handler, args=(tracker_ip, tracker_port), name="TrackerHandler", daemon=True)
    tracker_thread.start()
    
def init_peer(username, status="online"):
    """ Khởi tạo Peer với kết nối đến server """
    global my_username, my_status, my_listen_port, my_ip, client_socket
    my_username = username
    my_status = status
    tracker_ip = client.get_host_default_interface_ip()  
    tracker_port = 22236
    client_socket = client.create_client_socket(tracker_ip, tracker_port)
    my_listen_port = client_socket.getsockname()[1]  
    my_ip = client.get_host_default_interface_ip()

 
    # Hiển thị thông tin kết nối
    print(f"--- Khởi tạo Peer ---")
    print(f"  IP của bạn: {my_ip}")
    print(f"  Port lắng nghe P2P: {my_listen_port}")  # Sử dụng cổng từ client socket
    print(f"  Username: {my_username}")
    print(f"  Status: {my_status}")
    print(f"  Tracker: {tracker_ip}:{tracker_port}")
    print("--------------------")

    
    tracker_thread = threading.Thread(target=tracker_handler, args=(tracker_ip, tracker_port), name="TrackerHandler", daemon=True)

    tracker_thread.start()
