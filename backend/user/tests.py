from django.test import TestCase
import firebase_admin
from firebase_admin import credentials, auth
import requests
import json

class FirebaseTokenGenerationTestCase(TestCase):
     def test_custom_token_authentication(self):
          uid = "8jTawiVplrR1yGlqS4xTKPWEbuC2"

          # Generate a custom ID token for the specified user
          custom_token = auth.create_custom_token(uid)
          
          api_key = 'AIzaSyBVWm8Frug_qriTsokbIt3Ca2pVz7bkXe0'
          
          print(custom_token)