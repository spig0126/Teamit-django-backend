from django.test import TestCase
import firebase_admin
from firebase_admin import credentials, auth
import requests
import json
import base64
from rest_framework import status

class FirebaseTokenGenerationTestCase(TestCase):
     def test_custom_token_authentication(self):
          # 게더어스 운영진
          # uid = "g9qugqRFCogETrmpy7POSoluqIC2"
          # 부루정
          uid = "NecKBhN131PSsPuRfCVg1vDKjW03"
          # 그레기
          # uid = "JzlLAqlqOvPLAS2rwjKGrnCxE572"
          # 래빗
          # uid = "PsnFOUnlyJMFrd1uIX28EXdVA8g1"
          # 여니여니
          # uid = "oL9UK4B2wVQ7OYhTXdk3kwFP7Q02"
          # 티미_065
          # uid = "8jTawiVplrR1yGlqS4xTKPWEbuC2"
          # 개발자
          # uid = "kakao:3228496673"
          # 루루사탕
          # uid = "naver:NGf1vHub8F_xZ7LCJWnjIJWNPhAx0onfkb9qZ7s74KM"
          # 하이롱
          # uid = "kakao:3288498763"

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