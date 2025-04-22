import tkinter as tk
import re
import socket
import client
import threading

def register(username, password, confirm_password, label, window):
    """ Xác nhận đăng ký & gửi dữ liệu lên server nếu hợp lệ """
    if not validate_keyword(username) or not validate_keyword(password) or not validate_keyword(confirm_password):
        label.config(text="Sai quy cách đặt tên!", fg="red")
        return  

    if password != confirm_password:
        label.config(text="Mật khẩu không khớp!", fg="red")
        return  

    host = "10.28.128.17"
    port = 22236
    
    try:
        client_socket = client.create_client_socket(host, port)
        register_data = f"code:0:account:{username}:password:{password}"
        client_socket.sendall(register_data.encode())

        # Nhận phản hồi từ server
        threading.Thread(target=receive_response, args=(client_socket, window, label), daemon=True).start()
    
    except socket.error as e:
        label.config(text="Lỗi kết nối server!", fg="red")
        print("Lỗi socket:", e)

def receive_response(client_socket, window, label):
    """ Nhận phản hồi từ server & xử lý kết quả """
    try:
        response = client_socket.recv(1024).decode().strip()
        if response == "code:0:1":
            label.config(text="Đăng ký thành công!", fg="green")
            window.after(500, window.destroy)
        elif response == "code:0:0":
            label.config(text="Tài khoản đã tồn tại!", fg="red")
        else:
            label.config(text="Lỗi đăng ký! Vui lòng thử lại.", fg="red")
    finally:
        client_socket.close()

    
def open_register_window():
    """ Hiển thị màn hình đăng ký """
    register_window = tk.Toplevel()
    register_window.title("Đăng ký tài khoản")
    register_window.geometry("900x280")
    register_window.configure(bg="#87CEEB")

    entry_username = tk.Entry(register_window, width=30, fg="grey")
    entry_username.insert(0, "Tên đăng nhập")
    entry_username.bind("<FocusIn>", lambda event: (clear_placeholder(event, entry_username, "Tên đăng nhập"), show_popup(event, register_window)))
    entry_username.bind("<FocusOut>", lambda event: (restore_placeholder(event, entry_username, "Tên đăng nhập"), hide_popup()))
    entry_username.bind("<KeyRelease>", lambda event: validate_keyword(entry_username.get()))
    entry_username.bind("<Return>", lambda event: entry_password.focus())
    entry_username.pack(pady=5)

    entry_password = tk.Entry(register_window, width=30, fg="grey")
    entry_password.insert(0, "Mật khẩu")
    entry_password.bind("<FocusIn>", lambda event: (clear_placeholder(event, entry_password, "Mật khẩu"), show_popup(event, register_window)))
    entry_password.bind("<FocusOut>", lambda event: (restore_placeholder(event, entry_password, "Mật khẩu"), hide_popup()))
    entry_password.bind("<KeyRelease>", lambda event: validate_keyword(entry_password.get()))
    entry_password.bind("<Return>", lambda event: entry_confirm_password.focus())
    entry_password.pack(pady=5)

    entry_confirm_password = tk.Entry(register_window, width=30, fg="grey")
    entry_confirm_password.insert(0, "Nhập lại mật khẩu")
    entry_confirm_password.bind("<FocusIn>", lambda event: clear_placeholder(event, entry_confirm_password, "Nhập lại mật khẩu"))
    entry_confirm_password.bind("<FocusOut>", lambda event: restore_placeholder(event, entry_confirm_password, "Nhập lại mật khẩu"))
    entry_confirm_password.bind("<KeyRelease>", lambda event: validate_keyword(entry_confirm_password.get()))
    entry_confirm_password.bind("<Return>", lambda event: register(entry_username.get(), entry_password.get(), entry_confirm_password.get(), response_label, register_window))  # Enter → Xác nhận đăng ký
    entry_confirm_password.pack(pady=5)

    btn_confirm_register = tk.Button(register_window, text="Xác nhận đăng ký", bg="#347DBD", fg="white",
                                     command=lambda: register(entry_username.get(), entry_password.get(), entry_confirm_password.get(), response_label, register_window))
    btn_confirm_register.pack(pady=10)

    response_label = tk.Label(register_window, text="", bg="#87CEEB", fg="black", font=("Arial", 10))
    response_label.pack(pady=5)

    global popup_label
    popup_label = tk.Label(register_window, text="", bg="#FFC", fg="black", font=("Arial", 10), relief="solid", padx=5, pady=5)

def show_popup(event, window):
    """ Hiển thị hướng dẫn khi nhấn vào ô nhập """
    popup_label.config(text="📌 Quy tắc đặt tên:\n- Tài khoản hoặc mật khẩu phải >= 1 ký tự\n- Có thể chứa chữ cái Latin (A-Z, a-z) hoặc ký tự số (0-9)\n- Được phép ký tự đặc biệt, nhưng không chứa ':'")
    popup_label.place(x=event.widget.winfo_x() + 200, y=event.widget.winfo_y(), anchor="nw")

def hide_popup():
    """ Ẩn bảng hướng dẫn khi rời khỏi ô nhập """
    popup_label.place_forget()

    
def validate_keyword(text):
    """ Kiểm tra tài khoản & mật khẩu có hợp lệ không """
    return bool(re.match(r"^[a-zA-Z0-9!@#$%^&*()_+={}\[\],.?<>~-]+$", text))


def clear_placeholder(event, entry, default_text):
    """ Xóa chữ chìm khi chọn ô nhập (chỉ xóa nếu chưa thay đổi nội dung) """
    if entry.get() == default_text:  # Kiểm tra nếu vẫn là placeholder
        entry.delete(0, tk.END)  # Xóa chữ chìm
        entry.config(fg="black", show="*" if "Mật khẩu" in default_text or "Nhập lại mật khẩu" in default_text else "")  # Kiểm tra đúng cách

def restore_placeholder(event, entry, default_text):
    """ Hiển thị lại chữ chìm nếu ô nhập bị bỏ trống """
    if not entry.get():  # Kiểm tra nếu ô nhập trống
        entry.insert(0, default_text)
        entry.config(fg="grey", show="*" if "Mật khẩu" in default_text or "Nhập lại mật khẩu" in default_text else "")


