import requests

# create profile
create_endpoint = "http://localhost:8000/user/profile/"
data = {
     "user": {"id": 8},
     "visivility": "PI",
     "birthdate":"2000-01-01", 
     "sex": "F",
     "province_id": "1",
     "city_id": "2",
     "category": "PRO"
}
post_response = requests.post(create_endpoint, json=data)
print(post_response.json())