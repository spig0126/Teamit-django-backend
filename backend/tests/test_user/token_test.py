from django.test import TestCase
from firebase_admin import auth
import requests


def create_firebase_token(uid):
    custom_token = auth.create_custom_token(uid)
    encoded_token = custom_token.decode('utf-8')

    api_key = 'AIzaSyBVWm8Frug_qriTsokbIt3Ca2pVz7bkXe0'
    url = f'https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key={api_key}'
    response = requests.post(url,
                             headers={'Content-Type': 'application/json'},
                             json={'token': encoded_token, 'returnSecureToken': True})
    id_token = response.json().get('idToken')
    return id_token


class FirebaseTokenGenerationTestCase(TestCase):
    def test_external_api_call(self):
        # user_name = "와플"
        # uid = "와플"
        # user_name = "게더어스 운영진"
        # uid = "g9qugqRFCogETrmpy7POSoluqIC2"
        # 부루정
        # uid = "NecKBhN131PSsPuRfCVg1vDKjW03"
        # 그레기
        # uid = "JzlLAqlqOvPLAS2rwjKGrnCxE572"
        # 래빗
        # uid = "PsnFOUnlyJMFrd1uIX28EXdVA8g1"
        user_name = "여니여니"
        uid = "oL9UK4B2wVQ7OYhTXdk3kwFP7Q02"
        # 티미_065
        # uid = "8jTawiVplrR1yGlqS4xTKPWEbuC2"
        # user_name = "개발자"
        # uid = "kakao:3228496673"
        # user_name = "루루사탕"
        # uid = "naver:NGf1vHub8F_xZ7LCJWnjIJWNPhAx0onfkb9qZ7s74KM"
        # user_name = "하이롱"
        # uid = "kakao:3288498763"
        # 하이하이
        # uid = "Rk7eW278XAMC2SvHNX64OZBvxn23"
        # TeamTeam
        # uid = "kakao:3258297033"
        # Android
        # uid = "9m5Qj326mNd3QyX55oiAKNbMGOi2"
        # uid = "user profile test"
        # user_name = "팀합소"
        # uid = "FET8pxExb3TYTev5HfJzjDbFgzV2"

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
        print(user_name)
        print()
        print(id_token)
