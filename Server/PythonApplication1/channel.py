import json

def get_user_channels(username):
    try:
        # Đọc file channel.json
        with open("D:/Discord-like/Server/PythonApplication1/channel.json", "r", encoding='utf-8') as file:
            data = json.load(file)
        user_channels = []
        # Duyệt qua từng channel trong data
        for channel in data.get("channels", []):
            # Kiểm tra danh sách users trong channel
            for user in channel.get("users", []):
                if user.get("username") == username:
                    # Nếu tìm thấy username, thêm tên channel vào danh sách
                    user_channels.append(channel["name"])
                    break

        return user_channels
    except FileNotFoundError:
        print(f"[Error] Không tìm thấy file channel.json")
        return []
    except json.JSONDecodeError:
        print(f"[Error] File channel.json không đúng định dạng JSON")
        return []
    except Exception as e:
        print(f"[Error] Lỗi khi đọc file channel.json: {str(e)}")
        return []

def get_channel_members(channel_name):
    try:
        # Đọc file channel.json
        with open("D:/Discord-like/Server/PythonApplication1/channel.json", "r", encoding='utf-8') as file:
            data = json.load(file)
        # Duyệt qua từng channel trong data
        for channel in data.get("channels", []):
            if channel["name"] == channel_name:
                # Nếu tìm thấy kênh, trả về danh sách các thành viên trong kênh
                members = []
                for user in channel.get("users", []):
                    members.append({
                        "username": user["username"],
                        "status": user["status"]
                    })
                return members

        print(f"[Error] Không tìm thấy kênh có tên {channel_name}")
        return []

    except FileNotFoundError:
        print(f"[Error] Không tìm thấy file channel.json")
        return []
    except json.JSONDecodeError:
        print(f"[Error] File channel.json không đúng định dạng JSON")
        return []
    except Exception as e:
        print(f"[Error] Lỗi khi đọc file channel.json: {str(e)}")
        return []
    
def join_channel_on_server(username, channel_name, filename="D:/Discord-like/Server/PythonApplication1/channel.json"):
    try:
        # Đọc dữ liệu từ file JSON
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Kiểm tra nếu kênh tồn tại
        for channel in data["channels"]:
            if channel["name"] == channel_name:
                # Kiểm tra user đã có trong kênh chưa
                for user in channel["users"]:
                    if user["username"] == username:
                        return "2"  # User đã ở trong kênh, trả về "2"
                # Nếu chưa có, thêm user vào kênh
                channel["users"].append({"username": username, "status": "online"})  # Thêm với trạng thái mặc định
                # Ghi lại dữ liệu JSON sau khi cập nhật
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4)
                return "1"  # Tham gia thành công
        return "0"   
    except Exception as e:
        print(f"Lỗi khi xử lý tham gia kênh: {e}")
        return "-1" 
    
def add_channel(username, channel_name, filename="D:/Discord-like/Server/PythonApplication1/channel.json"):
    try:
        # Đọc file channel.json
        with open(filename, "r", encoding='utf-8') as f:
            data = json.load(f)

        # Kiểm tra xem kênh đã tồn tại hay chưa
        for channel in data.get("channels", []):
            if channel["name"] == channel_name:
                return "0"

        # Tạo mục kênh mới
        new_channel = {
            "name": channel_name,
            "users": [
                {
                    "username": username,
                    "status": "online"  # Mặc định trạng thái là online
                }
            ],
            "chat": f"{channel_name}_chat.json"
        }

        # Thêm kênh mới vào danh sách channels
        data["channels"].append(new_channel)

        # Ghi lại vào file channel.json
        with open("D:/Discord-like/Server/PythonApplication1/channel.json", "w", encoding='utf-8') as file:
            json.dump(data, file, indent=4, ensure_ascii=False)

        print(f"[Success] Đã tạo kênh '{channel_name}'.")
        return "1"

    except FileNotFoundError:
        print(f"[Error] Không tìm thấy file channel.json")
        return "0"
    
    except Exception as e:
        print(f"[Error] Lỗi khi thêm kênh: {str(e)}")
        return "0"

def get_online_users_in_channel(channel_name, filename="D:/Discord-like/Server/PythonApplication1/channel.json"):
    """Tìm danh sách user online trong kênh cụ thể"""
    try:
        with open(filename, "r", encoding='utf-8') as file:
            data = json.load(file)
        online_users = []
        
        # Duyệt từng channel để tìm kênh có tên trùng khớp
        for channel in data.get("channels", []):
            if channel.get("name") == channel_name:  # Nếu kênh khớp với `channel_name`
                for user in channel.get("users", []):
                    if user.get("status") == "online":  # Chỉ lấy user đang online
                        online_users.append(user.get("username"))
                break  # Thoát vòng lặp sau khi tìm thấy kênh
        
        return online_users
    except FileNotFoundError:
        print("[Error] Không tìm thấy file channel.json")
        return []
    except json.JSONDecodeError:
        print("[Error] File channel.json không đúng định dạng JSON")
        return []
    except Exception as e:
        print(f"[Error] Lỗi khi đọc file channel.json: {str(e)}")
        return []




