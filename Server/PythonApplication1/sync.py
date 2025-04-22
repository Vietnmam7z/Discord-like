import json

def get_connection_info(username, filename="D:/Discord-like/Server/PythonApplication1/connection.json"):
    with open(filename, "r", encoding="utf-8-sig") as f:
        data = json.load(f)  # Đọc dữ liệu JSON
 
    for connection in data["connections"]:
        if connection["username"] == username:  # Nếu username khớp
            return {"ip": connection["ip"], "port": connection["port"]}  # Trả về ip & port


def add_connection(username, ip, port, filename="D:/Discord-like/Server/PythonApplication1/connection.json"):
    with open(filename, "r", encoding="utf-8-sig") as f:
        data = json.load(f)  # Đọc dữ liệu JSON

    data["connections"].append({"username": username, "ip": ip, "port": port})

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def update_connection(username, new_ip, new_port, filename="D:/Discord-like/Server/PythonApplication1/connection.json"):
    with open(filename, "r", encoding="utf-8-sig") as f:
        data = json.load(f)  # Đọc dữ liệu JSON
    user_found = False
    for connection in data["connections"]:
        if connection["username"] == username:
            connection["ip"] = new_ip  # Cập nhật IP
            connection["port"] = new_port  # Cập nhật Port
            user_found = True
            break  # Thoát vòng lặp sau khi cập nhật

    # Nếu user không tồn tại, chạy hàm `add_connection()`
    if not user_found:
        add_connection(username, new_ip, new_port, filename)
    else:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)