from django.test import TestCase
from rest_framework.test import APIClient
import pytest

from user.models import *
from user.serializers import *


# class UserWithProfileTest(TestCase):
     # def setUp(self):
     #      self.client = APIClient()
     #      self.request_data = {
     #           "user": {
     #                "uid": "user profile test",
     #                "name": "user profile test",
     #                "avatar": "https://gatherus-s3.s3.amazonaws.com/avatars/4.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIA3AQ2SRW3QFHB5GF4%2F20231224%2Fap-northeast-2%2Fs3%2Faws4_request&X-Amz-Date=20231224T110114Z&X-Amz-Expires=3600&X-Amz-SignedHeaders=host&X-Amz-Signature=f585b8c7d97b5224a24730b632f3a13aeaa9d189f121e611c0d11f7f8e84d361",
     #                "background": "https://gatherus-s3.s3.amazonaws.com/backgrounds/6.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIA3AQ2SRW3QFHB5GF4%2F20231224%2Fap-northeast-2%2Fs3%2Faws4_request&X-Amz-Date=20231224T110118Z&X-Amz-Expires=3600&X-Amz-SignedHeaders=host&X-Amz-Signature=69a783f71fb67bd388316e788fb52f0b84153898ea4ae17efbdc3f16070373f6",
     #                "positions": ["영업"],
     #                "interests": ["여행", "금융"]
     #           },
     #           "birthdate": "1997-01-01",
     #           "sex": "M", 
     #           "short_pr": "영업 파이팅!",
     #           "activities": ["🔥 창업", "📚 스터디"],
     #           "cities": ["서울 서대문구", "경남 전체"]
     #      }
     #      self.user_instance = None
     #      self.profile_instance = None
     
     # def test_user_with_profile_create(self):
     #      # Create user with profile
     #      response = self.client.post('http://localhost:8001/api/users/', data=self.request_data, format='json')
     #      print(response.content)
     #      self.assertEqual(response.status_code, 201)
          
     #      # check if user and profile were created
     #      self.assertTrue(User.objects.filter(name='user profile test').exists())
     #      user = User.objects.get(name='user profile test')
     #      profile = user.profile
     #      self.assertIsNotNone(profile)
          
     #      # check M2M fields were successfully created
     #      interests_data = self.request_data['user']['interests']
     #      for priority, interest in enumerate(interests_data):
     #           self.assertTrue(UserInterest.objects.filter(user=user, interest=interest, priority=priority).exists())
     #      positions_data = self.request_data['user']['positions']
     #      for priority, position in enumerate(positions_data):
     #           self.assertTrue(UserPosition.objects.filter(user=user, position=position, priority=priority).exists())
     #      activities_data = self.request_data['activities']
     #      for priority, acitvity in enumerate(activities_data):
     #           self.assertTrue(UserPosition.objects.filter(user=user, acitvity=acitvity, priority=priority).exists())
     #      cities_data = self.request_data['cities']
     #      for priority, city in enumerate(cities_data):
     #           self.assertTrue(UserPosition.objects.filter(user=user, city=city, priority=priority).exists())
     #      self.assertEqual(user.main_interest, self.request_data['user']['interests'][0])
     #      self.assertEqual(user.main_position, self.request_data['user']['positions'][0])
     #      self.assertEqual(user.main_activity, self.request_data['activities'][0])
     #      self.assertEqual(user.main_city, self.request_data['cities'][0])
          
          # user.delete()
          # profile.delete()
     # @pytest.mark.django_db
     # def test(self):
     #      # response = self.client.post('http://localhost:8080/api/activities/', format='json')
     #      # print(response.content)
     #      print(Position.objects.all())