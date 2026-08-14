import logging

from django.conf import settings
from django.contrib.auth.models import Group

logger = logging.getLogger(__name__)


def sync_ldap_groups(sender, user, ldap_user, **kwargs):  # noqa: ARG001
    mapping = getattr(settings, 'LDAP_GROUP_MAP', {})
    if not mapping:
        return
    try:
        ldap_group_names = {str(g).lower() for g in ldap_user.group_names}
    except Exception:
        logger.warning('Could not resolve LDAP groups for user %s', user.email, exc_info=True)
        return
    for django_group, ldap_group_name in mapping.items():
        if str(ldap_group_name).lower() in ldap_group_names:
            group, _ = Group.objects.get_or_create(name=django_group)
            user.groups.add(group)
