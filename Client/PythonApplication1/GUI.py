import json
import re
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import json
import socket  # Thêm import socket
import tkinter.simpledialog
import peer
import chat
import threading
import time
import client
# Biến toàn cục lưu danh sách kênh
global_channels = []
global_members = []
global_chat = []

def update_list_channel(new_channels):
    global global_channels
    global_channels = new_channels

def update_chat_box():
    """Hiển thị nội dung `global_chat` lên `chat_box`"""
    chat_box.config(state=tk.NORMAL)  # Cho phép chỉnh sửa
    chat_box.delete("1.0", tk.END)  # Xóa nội dung cũ

    for msg in global_chat:
        formatted_msg = f"{msg['timestamp']} - {msg['sender']}: {msg['content']}\n"
        chat_box.insert(tk.END, formatted_msg)  # Thêm tin nhắn vào box chat

    chat_box.config(state=tk.DISABLED)

def receive_response():
    global global_members, global_chat
    try:
        response = peer.client_socket.recv(1024).decode()
        
        if response.startswith("code|2|"):
            parts = response.split("|")  # Chia thành 4 phần để tránh lỗi định dạng
            member_data = parts[2]# Dữ liệu danh sách thành viên
            chat_data = parts[3]  # Dữ liệu chat
            member_data = member_data.replace("'", '"')
            global_members = json.loads(member_data)  # Chuyển JSON thành danh sách Python
            global_chat = json.loads(chat_data) 
            update_chat_box()
            
        if response.startswith("code:4:"):
            parts = response.split(":")
            result = parts[2]
            if result == "1":
                messagebox.showinfo("Join Channel", "Join complete!")
            elif result == "2":
                messagebox.showwarning("Join Channel", "You already joined this channel!")
            elif result == "0":
                messagebox.showerror("Join Channel", "Invalid channel!")
                
        if response.startswith("code:5:"):
            parts = response.split(":")
            channel_list_json = parts[2]
            channel_list = json.loads(channel_list_json)
            update_list_channel(channel_list)
            print(channel_list)
            
        if response.startswith("code:6:"):
            parts = response.split(":")
            result = parts[2] 
            if result == "1":
                messagebox.showinfo("Create Channel", "Create complete!")
            elif result == "0":
                messagebox.showwarning("Create Channel", "Channel already created!")
           
        if response.startswith("code|7|"):
            parts = response.split("|") 
            chat_data = parts[2]  
            global_chat = json.loads(chat_data) 
            chat.mark_messages_as_sent()
            update_chat_box()
            
    except ConnectionError:
        print("[Error] Mất kết nối server!")
    except (ValueError, SyntaxError):
        print("[Error] Lỗi phân tích dữ liệu JSON-like trong phản hồi!")
    except Exception as e:
        print(f"[Error] Lỗi không xác định: {str(e)}")
   
def on_logout(*args):
    exit_command = f"code:3:{peer.my_username}:offline"
    peer.init_peer(peer.my_username, status="online")
    peer.client_socket.sendall(exit_command.encode())
    chat.clear_cache()
    root.destroy()
    
def show_main_ui():
    """ Hiển thị giao diện chính """
    global sidebar, sidebar_color, text_color, global_channels, channel_list, chat_header, peer, root, status_var, chat_box, channel_name

    root = tk.Toplevel()  # Sử dụng Toplevel thay vì Tk để không tạo vòng lặp chính mới
    root.title("Discord-like Chat")
    root.geometry("800x600")

    # Cấu hình màu sắc chủ đạo
    background_color = "#2f3136"
    sidebar_color = "#202225"
    button_color = "#7289da"
    hover_button_color = "#5a6f8e"
    message_box_color = "#40444b"
    text_color = "#ffffff"

    # Thanh điều hướng bên trái
    sidebar = tk.Frame(root, width=200, bg=sidebar_color, height=600)
    sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")

    # Tiêu đề sidebar
    sidebar_title = tk.Label(sidebar, text="Channels", font=("Arial", 18), fg=text_color, bg=sidebar_color, pady=20)
    sidebar_title.pack()

    # Listbox chứa các kênh
    channel_list = tk.Listbox(sidebar, bg=sidebar_color, fg=text_color, font=("Arial", 12), selectmode=tk.SINGLE, height=20, bd=0)
    for channel in global_channels:
        channel_list.insert(tk.END, channel)
    channel_list.pack(pady=20, fill=tk.BOTH, expand=True)
        
    # Khu vực trò chuyện chính
    chat_section = tk.Frame(root, bg=background_color)
    chat_section.grid(row=0, column=1, sticky="nsew")

    # Tiêu đề khu vực trò chuyện
    chat_header = tk.Label(chat_section, text="Select a channel", font=("Arial", 18), fg=text_color, bg=background_color, pady=20)
    chat_header.pack()
    
    user_frame = tk.Frame(chat_section, bg=background_color)
    user_frame.pack()

    # Label hiển thị tên người dùng
    user_label = tk.Label(user_frame, text=f"User: {peer.my_username}", font=("Arial", 14), fg=text_color, bg=background_color, pady=5)
    user_label.pack(side=tk.LEFT, padx=10)

    # Dropdown chọn trạng thái
    status_var = tk.StringVar()
    status_var.set("Online")  # Đặt giá trị mặc định là "Online"

    status_menu = ttk.Combobox(user_frame, textvariable=status_var, values=["Online", "Invisible"], state="readonly", width=10)
    status_menu.pack(side=tk.LEFT, padx=10)
    status_var.trace("w", update_status)
    
    # Frame chứa chat + thanh cuộn
    chat_frame = tk.Frame(chat_section, bg=background_color)
    chat_frame.pack(fill=tk.BOTH, expand=True)

    # Thanh cuộn
    chat_scrollbar = tk.Scrollbar(chat_frame)
    chat_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Khu vực tin nhắn
    chat_box = tk.Text(chat_frame, wrap=tk.WORD, state=tk.DISABLED, bg=message_box_color, 
                       fg=text_color, font=("Arial", 12), height=20, width=60, bd=0, 
                       yscrollcommand=chat_scrollbar.set)
    chat_box.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)

    # Khu vực nhập tin nhắn
    input_section = tk.Frame(root, bg=background_color, height=60)
    input_section.grid(row=1, column=1, sticky="ew")

    # Frame con để căn giữa các đối tượng
    center_frame = tk.Frame(input_section, bg=background_color)
    center_frame.pack(expand=True)

    # Ô nhập tin nhắn
    entry = tk.Entry(center_frame, bg="#40444b", fg=text_color, font=("Arial", 12), width=50, bd=0, relief="flat")
    entry.pack(side=tk.LEFT, padx=5, pady=10)

    # Bắt sự kiện nhấn "Enter" để gửi tin nhắn
    entry.bind("<Return>", lambda event: send_chat(entry))
    
    # Nút gửi tin nhắn
    send_button = tk.Button(center_frame, text="Gửi", command=lambda: send_chat(entry))
    send_button.pack(side=tk.LEFT, padx=5, pady=10)

    # Cập nhật khu vực trạng thái bên phải
    status_section = tk.Frame(root, bg=background_color)
    status_section.grid(row=0, column=2, sticky="nsew")
    # Nút đăng xuất
    logout_button = tk.Button(status_section, text="Log out", font=("Arial", 12), 
                              bg="#ff4d4d", fg="white", padx=10, pady=5, relief="flat", command=on_logout)
    logout_button.pack(pady=10, fill=tk.X)
    
    # Tiêu đề khu vực thành viên
    status_header = tk.Label(status_section, text="Members", font=("Arial", 18), fg=text_color, bg=background_color, pady=20)
    status_header.pack()

    # Danh sách thành viên động
    members_list = tk.Listbox(status_section, bg=background_color, fg=text_color, font=("Arial", 12), height=15, bd=0)
    members_list.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)

    join_button = tk.Button(sidebar, text="Join Channel", font=("Arial", 12), 
                            bg="#4CAF50", fg="white", padx=10, pady=5, relief="flat", command=join_channel)
    join_button.pack(pady=10, fill=tk.X)
    
    create_channel_button = tk.Button(sidebar, text="Create Channel", font=("Arial", 12),
                            bg="#4CAF50", fg="white", padx=10, pady=5, relief="flat", command=create_channel)
    create_channel_button.pack(pady=10, fill=tk.X)
    
    # Điều chỉnh kích thước và hiển thị giao diện
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(1, weight=3)  # Tăng trọng số cột giữa cho phần Chat
    root.grid_columnconfigure(2, weight=1)  # Giảm trọng số cột bên phải cho phần Members
    root.protocol("WM_DELETE_WINDOW", lambda: [chat.clear_cache(), root.destroy()])


    # Hàm thay đổi tiêu đề khi chọn kênh
    def change_chat_header(event):
        selected = channel_list.curselection()
        if selected:
            channel_name = channel_list.get(selected[0])    
            chat_header.config(text=f"#{channel_name}")        
            send_message(channel_name)
            receive_response()
            update_members()
            peer.client_socket.close()
            peer.reconnect(peer.my_username)
    
    # Gắn sự kiện thay đổi tiêu đề vào Listbox
    channel_list.bind("<<ListboxSelect>>", change_chat_header)

    # Hàm gửi lệnh với tên channel
    def send_message(channel_name):
        submit_command = f"code:2:{peer.my_listen_port}:{peer.my_username}:{channel_name}"
        peer.client_socket.sendall(submit_command.encode())
        print(f"Đã gửi lệnh: {submit_command}")
        
    def update_members():
        """Cập nhật danh sách thành viên từ `global_members` lên GUI"""
        members_list.delete(0, tk.END)  # Xóa danh sách cũ
        for member in global_members:
            members_list.insert(tk.END, f"{member['username']} ({member['status']})") 
    
    def send_chat(entry):
        selected = channel_list.curselection()
        if selected:
            channel_name = channel_list.get(selected[0])  
            content = entry.get().strip()  # Lấy nội dung nhập vào
            if content:
                channel = channel_name  # Lấy `channel_name` từ GUI
                chat.add_to_cache(channel, content)  # Gọi hàm lưu vào `cache.json`
                message = chat.get_unsent_messages()
                command = f"code:7:{peer.my_username}:{message}"  
                peer.client_socket.sendall(command.encode())
                receive_response()
                peer.client_socket.close()
                peer.reconnect(peer.my_username)
            if not content:
                message = chat.get_unsent_messages()
                if message != []:
                    command = f"code:7:{peer.my_username}:{message}"  
                    peer.client_socket.sendall(command.encode())
                    receive_response()
                    peer.client_socket.close()
                    peer.reconnect(peer.my_username)
            entry.delete(0, tk.END)          
            
def update_channel_list(new_channel_list):
    """Cập nhật danh sách kênh trên GUI"""
    channel_list.delete(0, tk.END)  # Xóa danh sách cũ
    channel_list.pack(pady=20, fill=tk.BOTH, expand=True)
    for channel in global_channels:
        channel_list.insert(tk.END, channel)  # Thêm danh sách mới

    print("Đã cập nhật danh sách kênh:", new_channel_list)
    
def update_status(*args):
    """Gửi lệnh khi trạng thái thay đổi"""
    peer.init_peer(peer.my_username, status="online")
    new_status = status_var.get()
    print(f"Đã đổi trạng thái thành {new_status}")
    exit_command = f"code:3:{peer.my_username}:{new_status.lower()}"  
    try:
        peer.client_socket.sendall(exit_command.encode())
        print(f"Đã gửi lệnh: {exit_command}")
    except Exception as e:
        print(f"Lỗi khi gửi lệnh: {e}")

def update_channel():
     command = f"code:5:{peer.my_username}"
     peer.client_socket.sendall(command.encode()) 
     receive_response()
     peer.client_socket.close()
     peer.reconnect(peer.my_username)
     update_channel_list(channel_list)
     
def join_channel():
    """Hiển thị hộp thoại nhập tên kênh và gửi lệnh tham gia"""
    channel_name = tkinter.simpledialog.askstring("Join Channel", "Nhập tên kênh:")
    join_command = f"code:4:{peer.my_username}:{channel_name}"
    try:
        peer.client_socket.sendall(join_command.encode())
        print(f"Đã gửi lệnh tham gia kênh: {join_command}")
    except Exception as e:
        print(f"Lỗi khi tham gia kênh: {e}")
    chat_header.config(text=f"#{channel_name}")
    receive_response()
    peer.client_socket.close()
    peer.reconnect(peer.my_username)
    update_channel()

def create_channel():
    channel_name = tkinter.simpledialog.askstring("Create Channel", "Nhập tên kênh:")
    create_command = f"code:6:{peer.my_username}:{channel_name}"
    try:
        peer.client_socket.sendall(create_command.encode())
        print(f"Đã gửi lệnh tạo kênh: {create_command}")
    except Exception as e:
        messagebox.showerror("Error", f"Cannot create channel: {e}")
    receive_response()
    peer.client_socket.close()
    peer.reconnect(peer.my_username)
    update_channel()

        


        
