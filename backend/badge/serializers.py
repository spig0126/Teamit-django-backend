from rest_framework import serializers
from urllib.parse import urlparse

from .models import *

BADGE_TITLES = {
    'attendance': '출석 도장 찍기',
    'team_participance': 'Join the team!',
    'team_post': '아아 알립니다',
    'liked': '넌 내가 찜했어',
    'recruit': '너 내 동료가 돼라',
    'team_refusal': '강철 심장',
    'user_profile': '위대한 첫걸음',
    'team_leader': '팀 리더',
    'shared_profile': '나로 말할 것 같으면',
    'early_user': '게더어스 행성의\n콜럼버스',
    'user_review': '여정을 함께해요'
}

BADGE_SUBTITLES = {
    'attendance': '근면 성실한 게더어스 러버',
    'team_participance': '게더어스 팀에 참여해보세요!',
    'team_post': '팀 게시글을 작성해보세요!',
    'liked': '누군가 날 찜했어요!',
    'recruit': '능력자들과 팀을 꾸려보세요!',
    'team_refusal': '실패하면 어때, 다시 해보면 되지!',
    'user_profile': '게더어스에 도착했어요',
    'team_leader': '내가 리더가 될 상인가?',
    'shared_profile': '프로필을 공유해봐요',
    'early_user': '게더어스를 발견한 첫 999명 중 한 명!',
    'user_review': '게더어스 능력자들에게 활동 후기를 남겨봐요!'
}

BADGE_NAME = {
    'attendance': '개근상',
    'team_participance': '팀플 마스터',
    'team_post': '쌩쌩 정보통',
    'liked': '슈퍼스타',
    'recruit': '헤드 헌터',
    'team_refusal': '',
    'user_profile': '',
    'team_leader': '',
    'shared_profile': '',
    'early_user': '',
    'user_review': '여정 기록가'
}

BADGE_LEVEL_DESCRIPTION = {
    'attendance': {
        1: '연속 5일 접속하기',
        2: '연속 14일 접속하기',
        3: '연속 25일 접속하기'
    },
    'team_participance': {
        1: '게더어스 팀 참여 1회(누적)',
        2: '게더어스 팀 참여 3회(누적)',
        3: '게더어스 팀 참여 5회(누적)'
    },
    'team_post': {
        1: '소속 팀 내 게시판 글 작성 5회',
        2: '소속 팀 내 게시판 글 작성 10회',
        3: '소속 팀 내 게시판 글 작성 30회'
    },
    'liked': {
        1: '날 찜한 사람 10명',
        2: '날 찜한 사람 30명',
        3: '날 찜한 사람 50명'
    },
    'recruit': {
        1: '팀장으로 팀원 5명 선발하기',
        2: '팀장으로 팀원 15명 선발하기',
        3: '팀장으로 팀원 30명 선발하기'
    },
    'team_refusal': {1: '팀 지원 5번 실패'},
    'user_profile': {1: '프로필 \'필수 정보\' + \'선택 정보\' 작성하기'},
    'team_leader': {1: '직접 팀 개설하기'},
    'shared_profile': {1: '공유 카드 1회 이상 공유하기\n(외부 링크, 카카오톡)'},
    'early_user': {1: '처음 게더어스 행성에 도착한\n전설의 999명 중 한 명'},
    'user_review': {
            1: '활동 후기 5개 남기기',
            2: '활동 후기 15개 남기기',
            3: '활동 후기 30개 남기기'
    },
}


class BadeDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = [
            'attendance_level',
            'user_review_level',
            'team_participance_level',
            'team_post_level',
            'early_user_status',
            'liked_level',
            'recruit_level',
            'team_refusal_status',
            'user_profile_status',
            'team_leader_status',
            'shared_profile_status',
        ]

    def transform_data(self, data, instance):
        result = []
        for field_name, value in data.items():
            badge_type = '_'.join(field_name.split('_')[:-1])
            img = []
            if type(value) is bool:
                img.append(default_storage.url(f'badges/{badge_type}.png'))
            else:
                for i in range(1, 4):
                    img.append(default_storage.url(f'badges/{badge_type}/{i}.png'))

            result.append({
                'title': BADGE_TITLES[badge_type],
                'subtitle': BADGE_SUBTITLES[badge_type],
                'name': BADGE_NAME[badge_type],
                'is_new': getattr(instance, f'{badge_type}_change'),
                'level': value,
                'img': img,
                'level_description': BADGE_LEVEL_DESCRIPTION[badge_type]
            })
        return result

    def to_representation(self, instance):
        data = super().to_representation(instance)
        transformed_data = self.transform_data(data, instance)
        return {'badges': transformed_data}


# field serializers
class BadgeImageField(serializers.Field):
    def to_internal_value(self, data):
        # Convert the signed url to image path
        try:
            parsed_url = urlparse(data)
            return parsed_url.path[1:]
        except:
            return f'badges/user_profile.png'

    def to_representation(self, value):
        return value
