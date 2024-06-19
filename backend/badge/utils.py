from .serializers import BADGE_TITLES
from fcm_notification.tasks import send_fcm_to_user_task
from django.core.files.storage import default_storage

def send_level_badge_fcm(user_pk, type, level):
     title = '배지 받아가세요!'
     body = '지금 바로 확인해보세요'
     data = {
          'page': 'badge',
          'title': BADGE_TITLES[type],
          'level': str(level),
          'img': default_storage.url(f'badges/{type}/{level}.png')
     }
     send_fcm_to_user_task.delay(user_pk, title, body, data)
     
def send_status_badge_fcm(user_pk, type):
     title = '배지 받아가세요!'
     body = '지금 바로 확인해보세요'
     data = {
          'page': 'badge',
          'title': BADGE_TITLES[type],
          'level': '0',
          'img': default_storage.url(f'badges/{type}.png')
     }
     send_fcm_to_user_task.delay(user_pk, title, body, data)