# -*- coding: utf-8 -*-
import socket
import threading
import json
import time
import argparse
import sys
import queue
import client

# --- Globals & Shared State ---
my_username = "DefaultUser"
my_status = "online"
my_listen_port = 0
my_ip = "" # Sẽ được lấy tự động
tracker_socket = None
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
    active_socket = None
    while not exit_flag.is_set():
        try:
            print(f"[TrackerClient] Đang kết nối đến Tracker {tracker_ip}:{tracker_port}...") # Dùng print thường
            active_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            active_socket.settimeout(10.0)
            active_socket.connect((tracker_ip, tracker_port))
            active_socket.settimeout(None)
            tracker_socket = active_socket
            print("[TrackerClient] Đã kết nối Tracker.") # Dùng print thường
            tracker_connected.set()

            submit_command = f"SUBMIT:{my_listen_port}:{my_username}:{my_status}"
            active_socket.sendall(submit_command.encode('utf-8'))
            print(f"[TrackerClient] Đã gửi: {submit_command.strip()}") # Dùng print thường

            while not exit_flag.is_set():
                # Gửi lệnh từ queue
                command_to_send = None
                try:
                    command_to_send = command_queue.get(timeout=0.1)
                    active_socket.sendall(command_to_send.encode('utf-8'))
                    safe_print(f"[TrackerClient] Đã gửi: {command_to_send.strip()}")
                    if command_to_send.strip().upper() == "DISCONNECT":
                        safe_print("[TrackerClient] Đã gửi DISCONNECT, đang thoát luồng tracker.")
                        time.sleep(0.5)
                        return
                except queue.Empty: pass
                except socket.error as e:
                     safe_print(f"[TrackerClient] Lỗi gửi lệnh đến Tracker: {e}. Đang thử kết nối lại...")
                     tracker_connected.clear()
                     break
                except Exception as e:
                     safe_print(f"[TrackerClient] Lỗi lấy lệnh từ queue: {e}")


                # Nhận phản hồi từ Tracker
                try:
                    active_socket.settimeout(0.1)
                    response_data = active_socket.recv(BUFFER_SIZE)
                    active_socket.settimeout(None)

                    response = response_data.decode('utf-8').strip()

                    parts = response.split(' ', 1)
                    response_command = parts[0].upper()

                    if response_command == "SUBMIT_OK":
                        safe_print("[TrackerClient] Tracker xác nhận SUBMIT.")
                    elif response_command == "PEERLIST" and len(parts) > 1:
                        try:
                            new_peer_list_data = json.loads(parts[1])
                            with peer_list_lock:
                                peer_list = new_peer_list_data
                            safe_print(f"[TrackerClient] Cập nhật danh sách peer: {len(peer_list)} peers.")
                        except json.JSONDecodeError as e:
                            safe_print(f"[TrackerClient] Lỗi giải mã JSON PEERLIST: {e}")
                    elif response_command == "ERROR":
                         safe_print(f"[TrackerClient] Tracker báo lỗi: {parts[1] if len(parts) > 1 else 'Unknown'}")
                    # --- TODO: Xử lý các phản hồi khác ---

                except socket.timeout: continue
                except socket.error as e:
                    safe_print(f"[TrackerClient] Lỗi nhận dữ liệu từ Tracker: {e}. Đang thử kết nối lại...")
                    tracker_connected.clear()
                    break
                except Exception as e:
                    safe_print(f"[TrackerClient] Lỗi xử lý phản hồi Tracker: {e}")

        except socket.timeout:
             print(f"[TrackerClient] Kết nối đến Tracker timeout. Đang thử lại...") # Dùng print thường
        except socket.error as e:
            print(f"[TrackerClient] Lỗi kết nối Tracker: {e}. Đang thử lại sau 5 giây...") # Dùng print thường
        except Exception as e:
             print(f"[TrackerClient] Lỗi không xác định: {e}. Đang thử lại sau 5 giây...") # Dùng print thường
        finally:
            tracker_connected.clear()
            if active_socket:
                try: active_socket.shutdown(socket.SHUT_RDWR)
                except: pass
                active_socket.close()
                active_socket = None
            if tracker_socket is active_socket: tracker_socket = None
            if not exit_flag.is_set(): time.sleep(5)

    safe_print("[TrackerClient] Luồng Tracker kết thúc.")
    if tracker_socket:
        try: tracker_socket.shutdown(socket.SHUT_RDWR)
        except: pass
        tracker_socket.close()
        tracker_socket = None

# --- P2P Message Sending ---
def send_p2p_message(target_ip, target_port, channel, message):
    """Gửi tin nhắn P2P đến một peer cụ thể."""
    p2p_socket = None
    try:
        p2p_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        p2p_socket.settimeout(P2P_CONNECT_TIMEOUT)
        p2p_socket.connect((target_ip, target_port))
        p2p_socket.settimeout(None)

        p2p_command = f"MSG {channel} {my_username} {message}\n"
        p2p_socket.sendall(p2p_command.encode('utf-8'))
        return True
    except socket.timeout:
        safe_print(f"[P2P Error] Timeout khi kết nối đến {target_ip}:{target_port}")
        return False
    except socket.error as e:
        safe_print(f"[P2P Error] Lỗi kết nối/gửi đến {target_ip}:{target_port}: {e}")
        return False
    except Exception as e:
        safe_print(f"[P2P Error] Lỗi không xác định khi gửi đến {target_ip}:{target_port}: {e}")
        return False
    finally:
        if p2p_socket: p2p_socket.close()

def init_peer(username, status="online"):
    """ Khởi tạo Peer với kết nối đến server """
    global my_username, my_status, my_listen_port, my_ip
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
    tracker_connected.wait(timeout=12.0)
    if not tracker_connected.is_set():
        print("[Main Warning] Không thể kết nối đến Tracker sau 12 giây.")

    safe_print("[Main] Đợi các hoạt động cuối cùng (tối đa vài giây)...")
    time.sleep(1.0)

    if client_socket:
        try:
            client_socket.close()  # Đóng kết nối sau khi sử dụng
        except:
            pass

    safe_print("[Main] Chương trình Peer đã thoát.")
    sys.exit(0)
