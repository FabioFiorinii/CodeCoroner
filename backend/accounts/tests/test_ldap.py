from unittest.mock import Mock

from django.contrib.auth.models import Group
from django.test import TestCase, override_settings

from accounts.models import User
from accounts.signals import sync_ldap_groups


class LdapGroupSyncTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='alice@codecoroner.dev', username='alice', password='x',
        )

    @override_settings(LDAP_GROUP_MAP={
        'default': 'ldap-users',
        'admins': 'ldap-admins',
    })
    def test_maps_matching_ldap_groups(self):
        ldap_user = Mock(group_names=[
            'Ldap-Users',
            'unrelated',
        ])
        sync_ldap_groups(None, self.user, ldap_user)

        self.user.refresh_from_db()
        names = set(self.user.groups.values_list('name', flat=True))
        self.assertIn('default', names)
        self.assertNotIn('admins', names)

    @override_settings(LDAP_GROUP_MAP={})
    def test_no_mapping_is_noop(self):
        sync_ldap_groups(None, self.user, Mock(group_names=['x']))
        self.user.refresh_from_db()
        self.assertEqual(self.user.groups.count(), 0)

    @override_settings(LDAP_GROUP_MAP={'default': 'ldap-users'})
    def test_group_lookup_failure_is_silent(self):
        ldap_user = Mock()
        ldap_user.group_names.side_effect = Exception('boom')
        sync_ldap_groups(None, self.user, ldap_user)
        self.user.refresh_from_db()
        self.assertEqual(self.user.groups.count(), 0)
        self.assertEqual(Group.objects.filter(name='default').count(), 0)
