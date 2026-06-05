import requests

res = requests.post("http://127.0.0.1:3000/api/courses/4", json={"name": "Golang", "videos": 5})
res = requests.put("http://127.0.0.1:3000/api/courses/1", json={"name": "GAY PORNO", "videos": 888})
print(res.json())
