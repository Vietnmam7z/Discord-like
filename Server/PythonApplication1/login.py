import json

def load_users():
    """ Đọc danh sách tài khoản từ file JSON """
    try:
        with open("users.json", "r") as file:
            data = json.load(file)
            return data.get("users", {})  # Trả về danh sách tài khoản
    except FileNotFoundError:
        return {}  # Nếu file không tồn tại, trả về danh sách rỗng

def verify_account(username, password):
    """ Kiểm tra tài khoản, trả về 1 nếu đúng, 0 nếu sai """
    users = load_users()
    if username in users and users[username] == password:
        return "1"  # Tài khoản hợp lệ
    return "0"  # Sai tài khoản hoặc mật khẩu
