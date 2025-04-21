import json

def load_users():
    """ Đọc danh sách tài khoản từ file JSON """
    try:
        with open("G:/Downloads/Discord-like/Server/PythonApplication1/users.json", "r") as file:
            data = json.load(file)
            return data.get("users", {})  # Trả về danh sách tài khoản
    except FileNotFoundError:
        return {}  # Nếu file không tồn tại, trả về danh sách rỗng

def update_user_status(username, filename="G:/Downloads/Discord-like/Server/PythonApplication1/channel.json"):
    """ Cập nhật trạng thái của user trong tất cả các kênh """
    try:
        # Đọc dữ liệu từ file JSON
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Duyệt qua tất cả các kênh
        for channel in data["channels"]:
            for user in channel["users"]:
                if user["username"] == username:
                    user["status"] = "online"  # Cập nhật trạng thái

        # Ghi dữ liệu đã chỉnh sửa trở lại file
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
            
    except Exception as e:
        print(f"Lỗi khi cập nhật JSON: {e}")
        
def verify_account(username, password):
    """ Kiểm tra tài khoản, trả về 1 nếu đúng, 0 nếu sai """
    users = load_users()
    if username in users and users[username] == password:
        update_user_status(username)
        return "1"  # Tài khoản hợp lệ
    return "0"  # Sai tài khoản hoặc mật khẩu