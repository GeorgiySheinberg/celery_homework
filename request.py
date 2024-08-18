import requests
import base64
import time



resp = requests.post('http://127.0.0.1:5000/upscale', files={
    'image_1': open('example/lama_300px.png', 'rb'),

})
resp_data = resp.json()
print(resp_data)
task_id, file_name = resp_data.get('task_id'), resp_data.get("file_name")


while True:
    resp = requests.get(f'http://127.0.0.1:5000/tasks/{task_id}')
    if resp.json().get("status") == 'PENDING':
        time.sleep(1)
    else:
        print(f'Ссылка на скачивание: http://127.0.0.1:5000/download/{file_name}')
        break