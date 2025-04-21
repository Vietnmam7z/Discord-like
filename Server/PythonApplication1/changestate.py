import json

def update_user_status(username, state, filename="G:/Downloads/Discord-like/Server/PythonApplication1/channel.json."):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)

        for channel in data["channels"]:
            for user in channel["users"]:
                if user["username"] == username:
                    user["status"] = state  # Cập nhật trạng thái

        # Ghi dữ liệu đã chỉnh sửa trở lại file
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    except Exception as e:
        print(f"Lỗi khi cập nhật JSON: {e}")