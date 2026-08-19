import os
import subprocess
import sys

import pytest

_PROD_ENV = {
    'DJANGO_SETTINGS_MODULE': 'config.settings.prod',
    'DJANGO_SECRET_KEY': 'test-only-strong-secret-for-settings-check',
    'DB_PASSWORD': 'test-only-db-password',
    'ALLOWED_HOSTS': 'codecoroner.example.com',
    'CORS_ALLOWED_ORIGINS': 'https://codecoroner.example.com',
    'CSRF_TRUSTED_ORIGINS': 'https://codecoroner.example.com',
}


def _run_prod(code: str, extra_env: dict[str, str] | None = None) -> str:
    env = {**os.environ, **_PROD_ENV, **(extra_env or {})}
    result = subprocess.run(
        [sys.executable, '-c', code],
        capture_output=True,
        text=True,
        env=env,
    )
    return result.stdout.strip()


def _settings_script(setting: str) -> str:
    return (
        'import django; django.setup(); from django.conf import settings; '
        f'print(repr(getattr(settings, "{setting}")))'
    )


class TestProdSettings:
    def test_secure_proxy_header_avoids_ssl_redirect_loop(self) -> None:
        assert (
            _run_prod(_settings_script('SECURE_PROXY_SSL_HEADER'))
            == "('HTTP_X_FORWARDED_PROTO', 'https')"
        )

    def test_security_headers_and_ssl_flags(self) -> None:
        for name, expected in {
            'DEBUG': 'False',
            'SECURE_SSL_REDIRECT': 'True',
            'CSRF_COOKIE_SECURE': 'True',
            'SESSION_COOKIE_SECURE': 'True',
            'SECURE_HSTS_SECONDS': '31536000',
        }.items():
            assert _run_prod(_settings_script(name)) == expected

    def test_csrf_trusted_origins_from_env(self) -> None:
        assert (
            _run_prod(_settings_script('CSRF_TRUSTED_ORIGINS'))
            == "['https://codecoroner.example.com']"
        )

    def test_csrf_trusted_origins_defaults_empty(self) -> None:
        script = _settings_script('CSRF_TRUSTED_ORIGINS')
        assert _run_prod(script, extra_env={'CSRF_TRUSTED_ORIGINS': ''}) == '[]'

    def test_missing_production_secrets_raise(self) -> None:
        code = 'import django; django.setup(); from django.conf import settings'
        for missing in ('DJANGO_SECRET_KEY', 'DB_PASSWORD'):
            env = {**os.environ, **_PROD_ENV}
            env[missing] = ''
            result = subprocess.run(
                [sys.executable, '-c', code],
                capture_output=True,
                text=True,
                env=env,
            )
            assert result.returncode != 0
            assert 'must be set to a non-default value in production' in result.stderr

    @pytest.mark.parametrize('debug_value', ['True', '1'])
    def test_debug_forced_false_in_prod(self, debug_value: str) -> None:
        env = {**os.environ, **_PROD_ENV, 'DJANGO_DEBUG': debug_value}
        result = subprocess.run(
            [sys.executable, '-c', _settings_script('DEBUG')],
            capture_output=True,
            text=True,
            env=env,
        )
        assert result.stdout.strip() == 'False'
