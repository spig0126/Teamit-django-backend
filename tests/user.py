import requests

# create user
create_endpoint = "http://localhost:8000/api/user/"
data = {
     "name": "test17", 
     "birthdata": "20010101",
     "sex": "F", 
     "activity": "전체",
     "position_names": ["금융/보험"], 
     "interest_names": ["asdfasdf", "공학"], 
     "province": "서울",
     "city": "서대문구"
}
post_response = requests.post(create_endpoint, json=data)
print(post_response.json())

# # retrieve user
# retrieve_endpoint = "http://localhost:8000/user/8/"
# get_response = requests.get(retrieve_endpoint)
# print(get_response.json())

# # check username availability
# check_endpoint = "http://localhost:8000/user/name/available/"
# data = {"name": "helo"}
# get_response = requests.post(check_endpoint, json=data)
# print(get_response.json())