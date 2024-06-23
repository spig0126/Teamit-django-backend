import pytest

class TestUserCreation():
    def test_user_image_file(self, user1):
        print(user1.avatar)
        assert str(user1.avatar)[:7] == 'avatars'