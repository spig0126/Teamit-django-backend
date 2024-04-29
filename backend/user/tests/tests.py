from django.test import TestCase
import firebase_admin
from firebase_admin import credentials, auth
import requests
import json
import base64
from unittest.mock import patch
import requests
from rest_framework import status

class FirebaseTokenGenerationTestCase(TestCase):
     def test_external_api_call(self):
          # 게더어스 운영진
          # uid = "g9qugqRFCogETrmpy7POSoluqIC2"
          # 부루정
          # uid = "NecKBhN131PSsPuRfCVg1vDKjW03"
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
          # 하이하이
          # uid = "Rk7eW278XAMC2SvHNX64OZBvxn23"
          # TeamTeam
          # uid = "kakao:3258297033"
          # Android
          # uid = "9m5Qj326mNd3QyX55oiAKNbMGOi2"
          uid = "user profile test"
          
          # Generate a custom ID token for the specified user
          custom_token = auth.create_custom_token(uid)
          encoded_token = custom_token.decode('utf-8')

          api_key = 'AIzaSyBVWm8Frug_qriTsokbIt3Ca2pVz7bkXe0'
          url = f'https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key={api_key}'
          response = requests.post(url, 
                                   headers={'Content-Type': 'application/json'},
                                   json={'token': encoded_token, 'returnSecureToken': True})
          
          # Ensure the request was successful
          self.assertEqual(response.status_code, 200)

          # Parse the ID token from the response
          id_token = response.json().get('idToken')

          # Optionally print the ID token to the console
          print()
          print(id_token)