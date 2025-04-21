import json
import time
def get_channel_chat(channel_name, filename_prefix="G:/Downloads/Discord-like/Server/PythonApplication1/chat/"):
    """Lấy toàn bộ dữ liệu chat từ file <channel_name>_chat.json"""
    chat_file = f"{filename_prefix}{channel_name}_chat.json"
    
    try:
        with open(chat_file, "r", encoding="utf-8-sig") as f:
            chat_data = json.load(f)          
        return json.dumps(chat_data.get("messages", []))  
    
    except FileNotFoundError:
        print(f"[Error] Không tìm thấy file chat: {chat_file}")
        return "[]"
    
    except json.JSONDecodeError as e:
        print(f"[Error] File chat bị lỗi JSON ({chat_file}): {str(e)}")
        return "[]"
    
def process_received_message(username, channel_name, message_data, base_path="G:/Downloads/Discord-like/Server/PythonApplication1/chat/"):
    """Xử lý dữ liệu chat, tìm file chat và ghi tin nhắn vào đó"""
    chat_file_path = f"{base_path}{channel_name}_chat.json"

    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")  # Lấy thời gian hiện tại
    new_message = {"sender": username, "timestamp": timestamp, "content": message_data}
    with open(chat_file_path, "r", encoding="utf-8-sig") as f:
        chat_data = json.load(f)
    chat_data["messages"].append(new_message)
    with open(chat_file_path, "w", encoding="utf-8") as f:
        json.dump(chat_data, f, indent=4, ensure_ascii=False)

import json

def create_chat_file(channel_name, base_path="G:/Downloads/Discord-like/Server/PythonApplication1/chat/"):
    chat_file_path = f"{base_path}{channel_name}_chat.json"
    chat_data = {"messages": []}  
    with open(chat_file_path, "w", encoding="utf-8") as f:
        json.dump(chat_data, f, indent=4, ensure_ascii=False)



