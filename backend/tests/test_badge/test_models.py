import pytest

from badge.models import BadgeLevels


@pytest.mark.django_db
def test_badge_creation(user1):
    assert user1.badge is not None


@pytest.mark.django_db
def test_badge_level(user1):
    badge = user1.badge
    assert badge.recruit_level is BadgeLevels.LEVEL_DEFAULT
    assert badge.team_participance_level is BadgeLevels.LEVEL_DEFAULT
    assert badge.attendance_level is BadgeLevels.LEVEL_DEFAULT

    badge.recruit_cnt = 5
    badge.team_participance_cnt = 1
    badge.attendance_cnt = 5
    assert badge.recruit_level is BadgeLevels.LEVEL_ONE
    assert badge.team_participance_level is BadgeLevels.LEVEL_ONE
    assert badge.attendance_level is BadgeLevels.LEVEL_ONE

    badge.recruit_cnt = 15
    badge.team_participance_cnt = 3
    badge.attendance_cnt = 14
    assert badge.recruit_level is BadgeLevels.LEVEL_TWO
    assert badge.team_participance_level is BadgeLevels.LEVEL_TWO
    assert badge.attendance_level is BadgeLevels.LEVEL_TWO
