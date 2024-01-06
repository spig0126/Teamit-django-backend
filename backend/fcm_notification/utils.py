import firebase_admin
from firebase_admin import messaging
from firebase_admin.exceptions import FirebaseError
from datetime import datetime, timedelta, timezone

from .models import *

def get_user_devices(user):
     return Device.objects.filter(user=user)

def get_team_members_devices(team):
     return [device for member in team.members.all() for device in get_user_devices(member)]

def check_device_token_freshness(device):
     seoul_timezone = timezone(timedelta(hours=9))
     two_months_ago = datetime.now(seoul_timezone) - timedelta(days=60)
     if device.timestamp < two_months_ago:
          # if older than 2 months, delete token
          device.delete()
          return None
     else:
          # if not, update timestamp
          device.save()
          return device

def send_fcm_message(device, title, body, data):
     if not device:
          print('error: token is not fresh')
          return
     
     message = messaging.Message(
               notification=messaging.Notification(
                    title=title,
                    body=body,
               ),
               token=device.token,
               data=data or None
          )

     try:
          messaging.send(message)
     except Exception as e:
          print('error: ', e)
          device.delete()
     
def send_fcm_to_user(user, title, body, data):
     devices = [check_device_token_freshness(device) for device in get_user_devices(user)]
     
     for device in devices:
          send_fcm_message(device, title, body, data)

def send_fcm_to_team(team, title, body, data):
     devices = [check_device_token_freshness(device) for device in get_team_members_devices(team)]
     for device in devices:
          send_fcm_message(device, title, body, data)