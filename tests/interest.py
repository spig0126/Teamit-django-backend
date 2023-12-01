import requests


endpoint = "http://localhost:8000/interest/5/"

get_response = requests.get(endpoint)
print(get_response.json())
