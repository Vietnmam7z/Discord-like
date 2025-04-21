from http import cookiejar
import tkinter as tk
import client
import socket
import threading
import peer
import GUI
import json

def login(username, password, login_window, response_label):
    """ Gửi thông tin đăng nhập đến server & xử lý phản hồi """
    if not username or not password or username == "Tên đăng nhập" or password == "Mật khẩu":
        return  

    host = client.get_host_default_interface_ip()
    port = 22236

    try:
        client_socket = client.create_client_socket(host, port)
        login_data = f"code:1:account:{username}:password:{password}"
        client_socket.sendall(login_data.encode())

        # Nhận phản hồi từ server & gọi Peer nếu đăng nhập thành công
        threading.Thread(target=receive_response, args=(client_socket, login_window, response_label, username), daemon=True).start()

    except socket.error as e:
        print(f"Lỗi kết nối: {e}")


def receive_response(client_socket, login_window, response_label, username):
    """ Nhận phản hồi từ server và hiển thị kết quả """
    peer_start = False  # Biến kiểm tra có khởi động Peer hay không

    try:
        response = client_socket.recv(1024).decode()
        if response.startswith("code:1:"):
            parts = response.split(":")
            if len(parts) > 3:
                result = parts[1]
                channel_list_json = parts[3]
                # Chuyển đổi JSON thành danh sách Python
                channel_list = json.loads(channel_list_json)
                GUI.update_list_channel(channel_list)
                response_label.config(text="Đăng nhập thành công", fg="green")  # Hiển thị chữ xanh
                login_window.after(500, login_window.destroy)  # Đóng cửa sổ sau 0.5 giây
                peer_start = True  # Đánh dấu để gọi Peer
        elif response == "code:1:0":
            response_label.config(text="Thông tin đăng nhập sai", fg="red")  # Hiển thị chữ đỏ

    except socket.timeout:
        response_label.config(text="Server không phản hồi!", fg="red")

    finally:
        client_socket.close()

        # Chỉ khởi động Peer nếu đăng nhập thành công
        if peer_start:
            peer.init_peer(username)
            GUI.show_main_ui()
            


def open_login_window():
    """ Hiển thị màn hình đăng nhập """
    login_window = tk.Toplevel()
    login_window.title("Đăng nhập")
    login_window.geometry("300x220")
    login_window.configure(bg="#87CEEB")

    entry_username = tk.Entry(login_window, width=30, fg="grey")
    entry_username.insert(0, "Tên đăng nhập")
    entry_username.bind("<FocusIn>", lambda event: clear_placeholder(event, entry_username, "Tên đăng nhập"))
    entry_username.bind("<FocusOut>", lambda event: restore_placeholder(event, entry_username, "Tên đăng nhập"))
    entry_username.bind("<Return>", lambda event: entry_password.focus())  # Nhấn Enter để xuống mật khẩu
    entry_username.pack(pady=5)

    entry_password = tk.Entry(login_window, width=30, fg="grey")
    entry_password.insert(0, "Mật khẩu")
    entry_password.bind("<FocusIn>", lambda event: clear_placeholder(event, entry_password, "Mật khẩu"))
    entry_password.bind("<FocusOut>", lambda event: restore_placeholder(event, entry_password, "Mật khẩu"))
    entry_password.bind("<Return>", lambda event: login(entry_username.get(), entry_password.get(), login_window, response_label))
    entry_password.pack(pady=5)

    # Nút hiện mật khẩu
    show_password_var = tk.BooleanVar()
    show_password_btn = tk.Checkbutton(login_window, text="Hiện mật khẩu", bg="#87CEEB", variable=show_password_var,
                                       command=lambda: toggle_password(entry_password, show_password_var))
    show_password_btn.pack(pady=5)

    btn_confirm = tk.Button(login_window, text="Đăng nhập", bg="#347DBD", fg="white",
                            command=lambda: login(entry_username.get(), entry_password.get(), login_window, response_label))
    btn_confirm.pack(pady=10)

    response_label = tk.Label(login_window, text="", bg="#87CEEB", fg="black", font=("Arial", 10))
    response_label.pack(pady=5)

def toggle_password(entry_password, var):
    """ Hiện hoặc ẩn mật khẩu khi chọn checkbox """
    entry_password.config(show="" if var.get() else "*")


def clear_placeholder(event, entry, default_text):
    """ Xóa văn bản mặc định khi chọn ô nhập """
    if entry.get() == default_text:
        entry.delete(0, tk.END)
        entry.config(fg="black", show="*" if default_text == "Mật khẩu" else "")

def restore_placeholder(event, entry, default_text):
    """ Khôi phục placeholder nếu để trống """
    if not entry.get():
        entry.insert(0, default_text)
        entry.config(fg="grey", show="" if default_text == "Tên đăng nhập" else "")
