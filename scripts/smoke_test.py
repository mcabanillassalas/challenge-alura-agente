import requests

payload = {"question": "¿De qué trata este manual?"}
response = requests.post("http://localhost:8000/api/v1/ask", json=payload, timeout=120)
print(response.status_code)
print(response.json())
