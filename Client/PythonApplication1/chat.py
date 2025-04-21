import json
import peer
def add_to_cache(channel, content, filename="G:/Downloads/Discord-like/Client/PythonApplication1/cache.json"):
    new_message = {"channel": channel, "content": content, "sent": 0}  # Tin nhắn mới
    with open(filename, "r", encoding="utf-8-sig") as f:
        cache_data = json.load(f)
    cache_data["messages"].append(new_message)

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(cache_data, f, indent=4, ensure_ascii=False)

def get_unsent_messages(filename="G:/Downloads/Discord-like/Client/PythonApplication1/cache.json"):
    with open(filename, "r", encoding="utf-8-sig") as f:
        cache_data = json.load(f)
    messages_to_send = []  # Danh sách tin nhắn cần gửi
    for msg in cache_data.get("messages", []):
        if msg["sent"] == 0:
            messages_to_send.append({"channel": msg["channel"], "content": msg["content"]})
    return messages_to_send  # Trả về danh sách tin nhắn chưa gửi

def mark_messages_as_sent(filename="G:/Downloads/Discord-like/Client/PythonApplication1/cache.json"):
    with open(filename, "r", encoding="utf-8-sig") as f:
        cache_data = json.load(f)
    for msg in cache_data.get("messages", []):
        if msg["sent"] == 0:
            msg["sent"] = 1  # Cập nhật trạng thái gửi
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(cache_data, f, indent=4, ensure_ascii=False)
        
def clear_cache(filename="G:/Downloads/Discord-like/Client/PythonApplication1/cache.json"):
    empty_cache = {"messages": []}  # Giữ cấu trúc JSON gốc nhưng xóa dữ liệu

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(empty_cache, f, indent=4, ensure_ascii=False)

    print(f"[Success] Đã xóa nội dung của `{filename}`!")
