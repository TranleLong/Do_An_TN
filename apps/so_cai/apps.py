from django.apps import AppConfig


class SoCaiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.so_cai'
    verbose_name = 'Sổ cái'

    def ready(self):
        from . import periods  # noqa: F401
