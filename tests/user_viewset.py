import requests

# # viewset user
# endpoint = "http://localhost:8000/api/users/8/"
# get_response = requests.get(endpoint)
# print(get_response.json())

# # create user
create_endpoint = "http://localhost:8000/api/users/"
# data = {"name": "test13", 
#      "position_names": [3, 4, 5, 2], 
#      "interest_names": [1, 2]}
data = {"name": "test14", 
     "position_names": ["영업", "디자인"], 
     "interest_names": ["게임", "공학"]}
post_response = requests.post(create_endpoint, json=data)
print(post_response.json())