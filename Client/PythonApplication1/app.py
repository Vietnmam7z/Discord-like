import tkinter as tk
import login  # Nhúng login.py để gọi hàm đăng nhập
import register 

def open_login():
    """ Gọi hàm hiển thị đăng nhập từ login.py """
    login.open_login_window()

# Tạo cửa sổ chính
root = tk.Tk()
root.title("BKcord88")
root.geometry("400x300")
root.configure(bg="#87CEEB")

# Tiêu đề
title_label = tk.Label(root, text="BKcord88", font=("Arial", 16, "bold"),
                       bg="#1E3A5F", fg="white", padx=10, pady=10)
title_label.pack(pady=15)


# Nút đăng nhập (Gọi login.py)
btn_login = tk.Button(root, text="Đăng nhập", font=("Arial", 12),
                      bg="#347DBD", fg="white", width=15, command=login.open_login_window)
btn_login.pack(pady=10)

# Nút đăng ký (Gọi register.py)
btn_register = tk.Button(root, text="Đăng ký", font=("Arial", 12),
                         bg="#2C7CBA", fg="white", width=15, command=register.open_register_window)
btn_register.pack(pady=10)

# Nút visitor mode (tạm thời chưa có chức năng)
btn_visitor = tk.Button(root, text="Visitor Mode", font=("Arial", 12),
                         bg="#347DBD", fg="white", width=15)
btn_visitor.pack(pady=10)

# Khởi động giao diện
root.mainloop()
