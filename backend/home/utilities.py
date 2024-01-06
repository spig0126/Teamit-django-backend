import requests
from rest_framework import status
from rest_framework.response import Response
from firebase_admin import auth
from django.core.files.storage import default_storage

def delete_s3_folder(folder_path):
     try:
          objects = default_storage.listdir(folder_path)
          files_to_delete = objects[1]  # List of files in the folder
          for file_name in files_to_delete:
               default_storage.delete(f"{folder_path}{file_name}")
          default_storage.delete(folder_path)
     except Exception as e:
          return Response({'detail': f'Failed to delete S3 folder. {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def fetch_user_info(access_token, login_type):
     api_url, headers, prefix = None, None, None
     
     if login_type == 'kakao':
          api_url = 'https://kapi.kakao.com/v2/user/me'
          headers = {
               'Authorization': f'Bearer {access_token}',
          }

     elif login_type == 'naver':
          api_url = "https://openapi.naver.com/v1/nid/me"
          headers = {
               "Authorization": f"Bearer {access_token}"
          }
      
     response = requests.get(api_url, headers=headers)
     user_info = None
     
     if response.status_code == 200:
          user_info = response.json()
          return user_info
     else:
          return None

def generate_firebase_custom_token(user_info, login_type):
     uid, email = None, None
     
     if login_type == 'kakao':
          id = user_info['id']
          uid = f'kakao:{id}'
          email = 'KAKAO.' + user_info['kakao_account']['email']
     elif login_type == 'naver':
          id = user_info['response']['id']
          uid = f'naver:{id}'
          email = 'NAVER.' + user_info['response']['email']
     try:
          auth.get_user(uid)
     except auth.UserNotFoundError:
          # If the user doesn't exist, create a new user with the UID
          auth.create_user(uid=uid, email=email)

     # Create a custom token
     try:
          custom_token = auth.create_custom_token(uid)
     except Exception as error:
          custom_token = None
     return custom_token