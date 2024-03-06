from rest_framework import serializers
from django.core.files.storage import default_storage

from .models import *

BADGE_TITLES = {
     'attendance': '출석 도장 찍기',
     'friendship': '사이좋게 지내자',
     'team_participance': 'Join the team!',
     'team_post': '아아 알립니다',
     'liked': '넌 내가 찜했어',
     'recruit': '너 내 동료가 돼라',
     'team_refusal': '강철 심장',
     'user_profile': '위대한 첫걸음', 
     'team_leader': '팀 리더', 
     'shared_profile': 'shared profile title',
     'review': '리뷰 남기기'
}

BADGE_SUBTITLES = {
     'attendance': '근면 성실한 게더어스 러버',
     'friendship': '게더어스의 능력자들과 친해져 봐요!',
     'team_participance': '게더어스 팀에 참여해보세요!',
     'team_post': '팀 게시글을 작성해보세요!',
     'liked': '누군가 날 찜했어요!',
     'recruit': '능력자들과 팀을 꾸려보세요',
     'team_refusal': '실패하면 어때, 다시 해보면 되지!',
     'user_profile': '게더어스에 도착했어요', 
     'team_leader': '내가 리더가 될 상인가?', 
     'shared_profile': 'shared profile subtitle',
     'review': '앱스토어에 리뷰 남기기'
}
class BadeDetailSerializer(serializers.ModelSerializer):
     class Meta:
          model = Badge
          fields = [
               'attendance_level', 
               'friendship_level',
               'team_participance_level',
               'team_post_level',
               'liked_level',
               'recruit_level',
               'team_refusal_status',
               'user_profile_status',
               'team_leader_status',
               'shared_profile_level',
               'review_status'
          ]
          
