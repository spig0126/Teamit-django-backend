from django.test import TestCase
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

# from user.models import User
from django.contrib.auth.models import User
from team.models import Team
from .models import Device  # Import your FCMToken model
from .utils import (
    get_user_devices,
    get_team_members_devices,
    check_device_token_freshness,
    send_fcm_message,
    send_fcm_to_user,
    send_fcm_to_team,
)

class FCMUtilsTestCase(TestCase):
     def setUp(self):
          # Create some sample FCM tokens with timestamps
          self.user3 = User.objects.create(pk=3, name='3', uid='3')
          self.user4 = User.objects.create(pk=4, name='4', uid='4')
          self.user5 = User.objects.create(pk=5, name='5', uid='5')
          self.user6 = User.objects.create(pk=6, name='6', uid='6')
          
          self.team1 = Team.objects.create(pk=1)
          self.team2 = Team.objects.create(pk=2)
          
          self.
          
          self.devices3_1= Device.objects.create(user=self.user3, token='3-1') 
          self.devices3_2= Device.objects.create(user=self.user3, token='3-2') 
          self.devices3_3= Device.objects.create(user=self.user3, token='3-3') 
          self.devices4_1= Device.objects.create(user=self.user4, token='4-1') 
          self.devices4_2= Device.objects.create(user=self.user4, token='4-2') 
          self.devices4_3= Device.objects.create(user=self.user4, token='4-3') 
          
          self.token3_1= self.devices3_1.token
          
     def test_get_user_tokens(self):
          tokens = get_user_tokens(self.user3)
          print('test_get_user_tokens', tokens)

     def test_get_team_members_tokens(self):
          tokens = get_team_members_tokens(self.team1)
          print('test_get_team_members_tokens', tokens)

     def test_check_token_freshness(self):
          two_months_ago = datetime.now() - timedelta(days=60)
          self.token1.timestamp = two_months_ago
          self.token1.save()

          # Check if token1 is older than 2 months
          result = check_token_freshness(self.token1)
          self.assertIsNone(result)
          self.assertEqual(FCMToken.objects.filter(id=self.token1.id).count(), 0)  # Token should be deleted

          # Check if token2 is fresh
          result = check_token_freshness(self.token2)
          self.assertIsNotNone(result)
          self.assertEqual(result, self.token2)

# #      def test_send_fcm_message(self):
# #           # Mock the messaging.send function
# #           with patch('firebase_admin.messaging.send', return_value='message_sent'):
# #                success, response = send_fcm_message(self.token1, 'Title', 'Body', {'key': 'value'})
# #                self.assertTrue(success)
# #                self.assertEqual(response, 'message_sent')

# #      def test_send_fcm_to_user(self):
# #           # Mock the check_token_freshness function
# #           with patch('your_app.utils.check_token_freshness', side_effect=lambda token: token):
# #                with patch('your_app.utils.send_fcm_message', return_value=(True, 'message_sent')):
# #                     results = send_fcm_to_user(self.user1, 'Title', 'Body', {'key': 'value'})

# #           self.assertEqual(len(results), 1)
# #           success, response = results[0]
# #           self.assertTrue(success)
# #           self.assertEqual(response, 'message_sent')

# #      def test_send_fcm_to_team(self):
# #           # Mock the check_token_freshness and send_fcm_message functions
# #           with patch('your_app.utils.check_token_freshness', side_effect=lambda token: token):
# #                with patch('your_app.utils.send_fcm_message', return_value=(True, 'message_sent')):
# #                     results = send_fcm_to_team(self.team, 'Title', 'Body', {'key': 'value'})

# #           self.assertEqual(len(results), 2)
# #           for success, response in results:
# #                self.assertTrue(success)
# #                self.assertEqual(response, 'message_sent')
# # `