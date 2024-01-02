from django.test import TestCase
import firebase_admin
from firebase_admin import credentials, auth
import requests
import json
import base64
from rest_framework import status

class FirebaseTokenGenerationTestCase(TestCase):
     def test_custom_token_authentication(self):
          uid = "OpEcOs2Z64R8tNnYUFmiGMJK3Yv1"

          api_key = 'AIzaSyBVWm8Frug_qriTsokbIt3Ca2pVz7bkXe0'
          # Generate a custom ID token for the specified user
          custom_token = auth.create_custom_token(uid)
          encoded_token = custom_token.decode('utf-8')
          
          print(custom_token)
          # # Define the URL for the authentication endpoint
          # url = 'https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key=AIzaSyBVWm8Frug_qriTsokbIt3Ca2pVz7bkXe0'

          # # Define the request data in the same format as the CURL request
          # data = {
          #      "token": encoded_token,
          #      "returnSecureToken": True
          # }
          # binary_data = bytes(json.dumps(data), 'utf-8')

          # # Send a POST request to the authentication endpoint
          # response = requests.post(url, json=data, headers={'Content-Type': 'application/json'})
          # print(response)
          # # Check if the response status code is 200 OK
          # self.assertEqual(response.status_code, status.HTTP_200_OK)

          # # Parse the JSON response data
          # response_data = response.json()
          # print(response_data)