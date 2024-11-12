from django.apps import AppConfig


class HomeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'home'

class MyAppConfig(AppConfig):
    name = 'my_app'

    def ready(self):
        import home.signals