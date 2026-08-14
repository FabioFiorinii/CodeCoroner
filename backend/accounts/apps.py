from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        try:
            from django_auth_ldap.backend import populate_user
        except ImportError:
            return
        from .signals import sync_ldap_groups

        populate_user.connect(sync_ldap_groups)
