import pytest
from django.core.files.storage import default_storage

from badge.models import BadgeLevels
from badge.serializers import BADGE_TITLES
from post.models import TeamPost
from review.models import UserReview
from tests.test_post.factories import TeamPostFactory
from team.models import TeamMembers
from tests.test_review.factories import UserReviewFactory
from tests.test_team.factories import TeamMemberFactory, TeamFactory, TeamApplicationFactory
from user.models import UserLikes
from tests.test_user.factories import UserFactory, UserExperienceFactory, UserExternalLinkFactory


@pytest.mark.django_db
def test_create_badge_and_count_user_signal():
    for _ in range(999):
        user = UserFactory()
        assert user.badge.early_user_status is True
        assert user.badge.early_user_change is True
    user = UserFactory()
    assert user.badge.early_user_status is False
    assert user.badge.early_user_change is False


@pytest.mark.django_db
class TestUpdateTeamParticipanceLevelSignal():
    def test_level_when_team_enter(self, user1):
        # test whether team_participance related fields/attributes are correctly updated
        badge = user1.badge
        assert badge.team_participance_level is BadgeLevels.LEVEL_DEFAULT

        # check change
        for _ in range(2):
            TeamMemberFactory(user=user1)
        assert badge.team_participance_cnt is 2
        assert badge.team_participance_change is True
        assert badge.team_participance_level is BadgeLevels.LEVEL_ONE

        # test no updates check no change after 5 teams
        for _ in range(6):
            TeamMemberFactory(user=user1)

        # check badge update
        assert badge.team_participance_cnt is 5
        assert badge.team_participance_change is True
        assert badge.team_participance_level is BadgeLevels.LEVEL_THREE

    def test_level_when_team_exit(self, user1):
        # check even after team exit, level is maintained
        badge = user1.badge

        for _ in range(2):
            TeamMemberFactory(user=user1)

        TeamMembers.objects.filter(user=user1).delete()
        assert badge.team_participance_cnt is 2
        assert badge.team_participance_change is True
        assert badge.team_participance_level is BadgeLevels.LEVEL_ONE

    def test_fcm_sent(self, user1, team2, mocker):
        mock_fcm = mocker.patch('fcm_notification.tasks.send_fcm_to_user_task.delay')

        TeamMemberFactory(team=team2, user=user1)

        expected_title = "배지 받아가세요!"
        expected_body = "지금 바로 확인해보세요"
        expected_data = {
            'title': BADGE_TITLES['team_participance'],
            'level': str(BadgeLevels.LEVEL_ONE),
            'img': default_storage.url(f'badges/team_participance/{BadgeLevels.LEVEL_ONE}.png')
        }

        mock_fcm.assert_called_once_with(user1.pk, expected_title, expected_body, expected_data)



@pytest.mark.django_db
class TestUpdateTeamPostLevelSignal():
    def test_level_update(self, team1, member1):
        # test update_team_post_level related fields/attributes are correctly updated
        badge = member1.user.badge
        assert badge.team_post_change is False
        assert badge.team_post_level is BadgeLevels.LEVEL_DEFAULT

        for _ in range(5):
            TeamPostFactory(writer=member1, post_to=team1)
        assert TeamPost.objects.filter(writer__user=member1.user).count() is 5
        assert badge.team_post_level is 1

        assert badge.team_post_change is True

        for _ in range(25):
            TeamPostFactory(writer=member1, post_to=team1)
        assert TeamPost.objects.filter(writer__user=member1.user).count() is 30
        assert badge.team_post_change is True
        assert badge.team_post_level is 3

    def test_fcm(self, user1, team1, member1, mocker):
        mock_fcm = mocker.patch('fcm_notification.tasks.send_fcm_to_user_task.delay')

        for _ in range(5):
            TeamPostFactory(writer=member1, post_to=team1)

        expected_title = "배지 받아가세요!"
        expected_body = "지금 바로 확인해보세요"
        expected_data = {
            'title': BADGE_TITLES['team_post'],
            'level': str(BadgeLevels.LEVEL_ONE),
            'img': default_storage.url(f'badges/team_post/{BadgeLevels.LEVEL_ONE}.png')
        }

        mock_fcm.assert_called_once_with(member1.user.pk, expected_title, expected_body, expected_data)


@pytest.mark.django_db
class TestUpdateRecruitLevelSignal():
    def test_level_update(self, badge1, user1):
        assert badge1.recruit_level is BadgeLevels.LEVEL_DEFAULT
        assert badge1.recruit_cnt is 0
        assert badge1.recruit_change is False

        team = TeamFactory(creator=user1)
        for _ in range(5):
            TeamMemberFactory(team=team)
        assert badge1.recruit_level is BadgeLevels.LEVEL_ONE
        assert badge1.recruit_cnt is 5
        assert badge1.recruit_change is True

        another_team = TeamFactory(creator=user1)
        for _ in range(10):
            TeamMemberFactory(team=another_team)
        assert badge1.recruit_level is BadgeLevels.LEVEL_TWO
        assert badge1.recruit_cnt is 15
        assert badge1.recruit_change is True

    def test_fcm(self, badge1, user1, team2, member1, mocker):
        users = []
        for i in range(5):
            user = UserFactory()
            TeamMemberFactory(user=user)
            users.append(user)

        mock_fcm = mocker.patch('fcm_notification.tasks.send_fcm_to_user_task.delay')

        team = TeamFactory(creator=user1)
        for i in range(5):
            TeamMemberFactory(team=team, user=users[i])

        expected_title = "배지 받아가세요!"
        expected_body = "지금 바로 확인해보세요"
        expected_data = {
            'title': BADGE_TITLES['recruit'],
            'level': str(BadgeLevels.LEVEL_ONE),
            'img': default_storage.url(f'badges/recruit/{BadgeLevels.LEVEL_ONE}.png')
        }

        mock_fcm.assert_called_once_with(user1.pk, expected_title, expected_body, expected_data)


@pytest.mark.django_db
class TestUpdateLikedLevelSignal():
    def test_level_update(self, badge1, user1):
        assert UserLikes.objects.filter(to_user=user1).count() is 0
        assert badge1.liked_level is BadgeLevels.LEVEL_DEFAULT
        assert badge1.liked_change is False

        for _ in range(10):
            from_user = UserFactory()
            UserLikes.objects.create(from_user=from_user, to_user=user1)
        assert UserLikes.objects.filter(to_user=user1).count() is 10
        assert badge1.liked_level is BadgeLevels.LEVEL_ONE
        assert badge1.liked_change is True

    def test_fcm(self, badge1, user1, mocker):
        users = [UserFactory() for _ in range(10)]

        mock_fcm = mocker.patch('fcm_notification.tasks.send_fcm_to_user_task.delay')

        for from_user in users:
            UserLikes.objects.create(from_user=from_user, to_user=user1)

        expected_title = "배지 받아가세요!"
        expected_body = "지금 바로 확인해보세요"
        expected_data = {
            'title': BADGE_TITLES['liked'],
            'level': str(BadgeLevels.LEVEL_ONE),
            'img': default_storage.url(f'badges/liked/{BadgeLevels.LEVEL_ONE}.png')
        }

        mock_fcm.assert_called_once_with(user1.pk, expected_title, expected_body, expected_data)


@pytest.mark.django_db
class TestUpdateUserReviewLevelSignal():
    def test_level_update(self, badge1, user1):
        assert badge1.user_review_cnt is 0
        assert badge1.user_review_level is BadgeLevels.LEVEL_DEFAULT
        assert badge1.user_review_change is False

        for _ in range(5):
            UserReviewFactory(reviewer=user1)

        assert badge1.user_review_cnt is 5
        assert badge1.user_review_level is BadgeLevels.LEVEL_ONE
        assert badge1.user_review_change is True

    def test_level_not_updated(self, badge1, user1):
        assert badge1.user_review_cnt is 0
        assert badge1.user_review_level is BadgeLevels.LEVEL_DEFAULT
        assert badge1.user_review_change is False

        for _ in range(4):
            UserReviewFactory(reviewer=user1)

        review = UserReview.objects.filter(reviewer=user1).first()
        review.content = 'update_content'
        review.save()

        assert badge1.user_review_cnt is 4
        assert badge1.user_review_level is BadgeLevels.LEVEL_DEFAULT
        assert badge1.user_review_change is False


    def test_fcm_sent(self, badge1, user1, mocker):
        users = [UserFactory() for _ in range(15)]

        mock_fcm = mocker.patch('fcm_notification.tasks.send_fcm_to_user_task.delay')

        for reviewee in users:
            UserReviewFactory(reviewer=user1, reviewee=reviewee)

        expected_title = "배지 받아가세요!"
        expected_body = "지금 바로 확인해보세요"
        expected_data1 = {
            'title': BADGE_TITLES['user_review'],
            'level': str(BadgeLevels.LEVEL_ONE),
            'img': default_storage.url(f'badges/user_review/{BadgeLevels.LEVEL_ONE}.png')
        }
        expected_data2 = {
            'title': BADGE_TITLES['user_review'],
            'level': str(BadgeLevels.LEVEL_TWO),
            'img': default_storage.url(f'badges/user_review/{BadgeLevels.LEVEL_TWO}.png')
        }

        calls = [
            mocker.call(user1.pk, expected_title, expected_body, expected_data1),
            mocker.call(user1.pk, expected_title, expected_body, expected_data2)
        ]

        mock_fcm.assert_has_calls(calls)
        assert mock_fcm.call_count == 2



@pytest.mark.django_db
class TestUpdateTeamRefusalStatusSignal():
    def test_status_update(self, user1, badge1, team2):
        assert badge1.team_refusal_status is False
        assert badge1.team_refusal_change is False

        application = TeamApplicationFactory(team=team2, applicant=user1)
        application.accepted = False
        application.save()

        assert badge1.team_refusal_status is True
        assert badge1.team_refusal_change is True

    def test_fcm_sent(self, user1, team2, mocker):
        mock_fcm = mocker.patch('fcm_notification.tasks.send_fcm_to_user_task.delay')

        application = TeamApplicationFactory(team=team2, applicant=user1)
        application.accepted = False
        application.save()

        expected_title = "배지 받아가세요!"
        expected_body = "지금 바로 확인해보세요"
        expected_data = {
            'title': BADGE_TITLES['team_refusal'],
            'level': '0',
            'img': default_storage.url(f'badges/team_refusal.png')
        }

        mock_fcm.assert_called_once_with(user1.pk, expected_title, expected_body, expected_data)

    def test_fcm_not_sent(self, user1, team2, mocker):
        application = TeamApplicationFactory(applicant=user1)
        application.accepted = False
        application.save()

        mock_fcm = mocker.patch('fcm_notification.tasks.send_fcm_to_user_task.delay')
        another_application = TeamApplicationFactory(team=team2, applicant=user1)
        another_application.accepted = False
        another_application.save()

        mock_fcm.assert_not_called()


@pytest.mark.django_db
class TestUpdateUserProfileStatusSignal():
    def test_status_update(self, user1, badge1):
        assert badge1.user_profile_status is False
        assert badge1.user_profile_change is False

        profile = user1.profile
        profile.education = '게더어스대학교'
        profile.keywords = '#성실'
        profile.tools = 'Github, Pycharm'
        profile.certificates = 'TOEIC'
        profile.save()

        assert badge1.user_profile_status is False
        assert badge1.user_profile_change is False

        UserExperienceFactory(user_profile=profile)
        UserExternalLinkFactory(user_profile=profile)
        profile.save()

        assert badge1.user_profile_status is True
        assert badge1.user_profile_change is True

    def test_fcm_sent(self, user1, mocker):
        mock_fcm = mocker.patch('fcm_notification.tasks.send_fcm_to_user_task.delay')

        profile = user1.profile
        profile.education = '게더어스대학교'
        profile.keywords = '#성실'
        profile.tools = 'Github, Pycharm'
        profile.certificates = 'TOEIC'
        UserExperienceFactory(user_profile=profile)
        UserExternalLinkFactory(user_profile=profile)
        profile.save()

        expected_title = "배지 받아가세요!"
        expected_body = "지금 바로 확인해보세요"
        expected_data = {
            'title': BADGE_TITLES['user_profile'],
            'level': '0',
            'img': default_storage.url(f'badges/user_profile.png')
        }

        mock_fcm.assert_called_once_with(user1.pk, expected_title, expected_body, expected_data)

    def test_fcm_not_sent(self, user1, mocker):
        profile = user1.profile
        profile.education = '게더어스대학교'
        profile.keywords = '#성실'
        profile.tools = 'Github, Pycharm'
        profile.certificates = 'TOEIC'
        UserExperienceFactory(user_profile=profile)
        UserExternalLinkFactory(user_profile=profile)
        profile.save()

        mock_fcm = mocker.patch('fcm_notification.tasks.send_fcm_to_user_task.delay')

        UserExperienceFactory(user_profile=profile)
        profile.save()

        mock_fcm.assert_not_called()


@pytest.mark.django_db
class TestUpdateTeamLeaderStatusSignal():
    def test_status_update(self, user1, badge1):
        assert badge1.team_leader_status is False
        assert badge1.team_leader_change is False

        TeamFactory(creator=user1)

        assert badge1.team_leader_status is True
        assert badge1.team_leader_change is True

    def test_fcm_sent(self, user1, mocker):
        mock_fcm = mocker.patch('fcm_notification.tasks.send_fcm_to_user_task.delay')

        TeamFactory(creator=user1)

        expected_title = "배지 받아가세요!"
        expected_body = "지금 바로 확인해보세요"
        expected_data = {
            'title': BADGE_TITLES['team_leader'],
            'level': '0',
            'img': default_storage.url(f'badges/team_leader.png')
        }

        mock_fcm.assert_called_once_with(user1.pk, expected_title, expected_body, expected_data)

    def test_fcm_not_sent(self, user1, badge1, mocker):
        TeamFactory(creator=user1)

        mock_fcm = mocker.patch('fcm_notification.tasks.send_fcm_to_user_task.delay')

        TeamFactory(creator=user1)

        mock_fcm.assert_not_called()

