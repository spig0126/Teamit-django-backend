from django.utils import timezone
from urllib.parse import urlencode
from django.core.files.storage import default_storage
from rest_framework import status

from badge.models import BadgeLevels
from badge.serializers import BADGE_TITLES
from user.models import User


class TestViewChangedBadgeAPIView():
    def test_update_badge_change_status(self, user1, badge1, api_client):
        for badge_type in BADGE_TITLES.keys():
            setattr(badge1, f'{badge_type}_change', True)
            badge1.save()

        for badge_type in BADGE_TITLES.keys():
            assert getattr(badge1, f'{badge_type}_change')

            base_url = '/api/badges/viewed/'
            title = BADGE_TITLES[badge_type]
            query_params = urlencode({'title': title})
            url = f'{base_url}?{query_params}'
            response = api_client.put(url, {'title': title}, format='json')

            assert response.status_code == status.HTTP_200_OK
            badge1.refresh_from_db()
            assert getattr(badge1, f'{badge_type}_change') is False

    def test_invalid_title_parameter(self, api_client):
        for badge_type in BADGE_TITLES.keys():
            base_url = '/api/badges/viewed/'
            title = BADGE_TITLES[badge_type]
            query_params = urlencode({'title': ''})
            url = f'{base_url}?{query_params}'
            response = api_client.put(url, {'title': title}, format='json')

            assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_missing_title_parameter(self, user1, badge1, api_client):
        base_url = '/api/badges/viewed/'
        response = api_client.put(base_url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestUpdateUserLastLoginTimeAPIView():
    def setup_method(self):
        self.yesterday_1159pm = (timezone.now() - timezone.timedelta(days=1)).replace(hour=23, minute=59, second=59)
        self.two_days_ago = timezone.now() - timezone.timedelta(days=2)

    def test_sequential_login(self, user1, badge1, api_client):
        assert badge1.attendance_cnt is 0
        assert badge1.attendance_level is BadgeLevels.LEVEL_DEFAULT
        assert badge1.attendance_change is False

        User.objects.filter(pk=user1.pk).update(last_login_time=self.yesterday_1159pm)

        response = api_client.put('/api/badges/attendance/')

        badge1.refresh_from_db()
        assert response.status_code == status.HTTP_200_OK
        assert badge1.attendance_cnt is 1
        assert badge1.attendance_level is 0
        assert badge1.attendance_change is False

        badge1.attendance_cnt = 4
        badge1.save()
        User.objects.filter(pk=user1.pk).update(last_login_time=self.yesterday_1159pm)

        response = api_client.put('/api/badges/attendance/')
        badge1.refresh_from_db()
        assert response.status_code == status.HTTP_200_OK
        assert badge1.attendance_cnt is 5
        assert badge1.attendance_level is 1
        assert badge1.attendance_change is True

    def test_unsequential_login(self, user1, badge1, api_client):
        badge1.attendance_cnt = 14
        badge1.attendance_level = 2
        badge1.save()
        assert badge1.attendance_cnt is 14
        assert badge1.attendance_level is 2

        User.objects.filter(pk=user1.pk).update(last_login_time=self.two_days_ago)

        response = api_client.put('/api/badges/attendance/')
        badge1.refresh_from_db()
        assert response.status_code == status.HTTP_200_OK
        assert badge1.attendance_cnt is 0
        assert badge1.attendance_level is 2

    def test_fcm_sent(self, user1, badge1, api_client, mocker):
        badge1.attendance_cnt = 4
        badge1.attendance_level = 0
        badge1.save()
        User.objects.filter(pk=user1.pk).update(last_login_time=self.yesterday_1159pm)

        mock_fcm = mocker.patch('fcm_notification.tasks.send_fcm_to_user_task.delay')

        response = api_client.put('/api/badges/attendance/')

        expected_title = "배지 받아가세요!"
        expected_body = "지금 바로 확인해보세요"
        expected_data = {
            'title': BADGE_TITLES['attendance'],
            'level': str(BadgeLevels.LEVEL_ONE),
            'img': default_storage.url(f'badges/attendance/{BadgeLevels.LEVEL_ONE}.png')
        }

        mock_fcm.assert_called_once_with(user1.pk, expected_title, expected_body, expected_data)

    def test_fcm_not_sent(self, user1, badge1, api_client, mocker):
        # 연속 출첵했지만 배지 단계에 도달하지 못한 경우
        mock_fcm = mocker.patch('fcm_notification.tasks.send_fcm_to_user_task.delay')
        response = api_client.put('/api/badges/attendance/')
        mock_fcm.assert_not_called()

        # 연속 출첵하지 않아 출첵수 초기화된 경우
        mock_fcm = mocker.patch('fcm_notification.tasks.send_fcm_to_user_task.delay')
        badge1.attendance_cnt = 4
        badge1.attendance_level = 0
        badge1.save()
        User.objects.filter(pk=user1.pk).update(last_login_time=self.two_days_ago)

        response = api_client.put('/api/badges/attendance/')

        mock_fcm.assert_not_called()

