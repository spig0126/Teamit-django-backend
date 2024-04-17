from django.apps import AppConfig


class ProfileCardConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "profile_card"
    
    def ready(self):
        from . import signals
