from celery import shared_task
from firebase_admin import messaging
from datetime import datetime, timedelta, timezone

from .models import *


@shared_task
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


@shared_task
def send_fcm_message_task(token, title, body, data):
    if not token:
        return
    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        token=token,
        data=data or None
    )

    try:
        messaging.send(message)
    except Exception as e:
        print(e)


@shared_task
def send_fcm_to_user_task(user_pk, title, body, data):
    user_devices = Device.objects.filter(user=user_pk)
    results = []
    for device in user_devices:
        device = check_device_token_freshness(device)
        if device:
            result = send_fcm_message_task.delay(device.token, title, body, data)
            results.append(result)
