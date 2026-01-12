import requests
import threading

URL = "http://127.0.0.1:8000/events"

def send_event(event_id):
    payload = {
        "event_id": event_id,
        "event_type": "MESSAGE_RECEIVED",
        "payload": {}
    }
    r = requests.post(URL, json=payload)
    print(event_id, r.status_code, r.json())

threads = []

for i in range(2):
    t = threading.Thread(target=send_event, args=(f"con-{i}",))
    threads.append(t)
    t.start()

for t in threads:
    t.join()

