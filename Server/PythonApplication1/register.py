import json

def load_users():
    """ Đọc danh sách tài khoản từ users.json """
    try:
        with open("D:/Discord-like/Server/PythonApplication1/users.json", "r") as file:
            users = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        users = {}  # Nếu file không tồn tại hoặc lỗi, tạo danh sách rỗng
    return users

def save_users(users):
    """ Lưu danh sách tài khoản vào users.json """
    with open("D:/Discord-like/Server/PythonApplication1/users.json", "w") as file:
        json.dump(users, file, indent=4)

def register_account(username, password):
    """ Đăng ký tài khoản mới nếu chưa tồn tại """
    users = load_users()
    if username in users["users"]:  # Nếu tài khoản đã tồn tại
        return "0"  # Trả về mã báo lỗi tài khoản đã tồn tại
    else:
        users["users"][username] = password  # Lưu tài khoản mới
        save_users(users)
        return "1"  # Trả về mã xác nhận đăng ký thành công
