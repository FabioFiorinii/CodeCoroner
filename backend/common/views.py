import httpx
from django.conf import settings
from django.db import connection
from rest_framework import permissions, serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import PlatformSetting

AI_ENGINE_URL = getattr(settings, 'AI_ENGINE_URL', 'http://ai-engine:8002')
PULL_TIMEOUT = 1800
TEST_TIMEOUT = 600
MODELS_TIMEOUT = 10


class IsSuperUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_superuser


def _error_detail(resp):
    try:
        return resp.json().get('detail', '')
    except Exception:
        return ''


class HealthView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, _request):
        db_ok = True
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
        except Exception:
            db_ok = False
        ai_ok = False
        try:
            resp = httpx.get(f'{AI_ENGINE_URL}/health', timeout=5)
            ai_ok = resp.status_code == 200
        except Exception:
            ai_ok = False
        status = 'healthy' if (db_ok and ai_ok) else 'degraded'
        return Response({
            'status': status,
            'database': db_ok,
            'ai_engine': ai_ok,
        })


class ModelSettingsSerializer(serializers.Serializer):
    tier = serializers.ChoiceField(choices=list(settings.MODEL_TIERS.keys()))


PIPELINE_STEPS = [
    'analyze_input',
    'bug_localization',
    'root_cause',
    'fix_suggestion',
    'generate_report',
]


class ModelSettingsView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsSuperUser]

    @staticmethod
    def _pipeline_map(setting):
        disabled = set(setting.disabled_pipeline_steps or [])
        return {step: step not in disabled for step in PIPELINE_STEPS}

    def _installed_models(self):
        try:
            resp = httpx.get(f'{AI_ENGINE_URL}/models', timeout=MODELS_TIMEOUT)
            resp.raise_for_status()
            return set(resp.json().get('models', []))
        except Exception:
            return set()

    def _ensure_usable(self, model):
        installed = self._installed_models()
        if model not in installed:
            resp = httpx.post(
                f'{AI_ENGINE_URL}/pull-model',
                json={'model': model},
                timeout=PULL_TIMEOUT,
            )
            if resp.status_code != 200:
                raise RuntimeError(_error_detail(resp) or f'Model {model} could not be downloaded')
        resp = httpx.post(
            f'{AI_ENGINE_URL}/test-model',
            json={'model': model},
            timeout=TEST_TIMEOUT,
        )
        if resp.status_code != 200:
            raise RuntimeError(_error_detail(resp) or f'Model {model} downloaded but failed verification')

    def get(self, request):
        setting = PlatformSetting.get_solo()
        installed = self._installed_models()
        available = []
        for key, cfg in settings.MODEL_TIERS.items():
            models = list(dict.fromkeys([cfg['llm_model'], cfg['rca_model']]))
            available.append({
                'key': key,
                'label': cfg['label'],
                'model': models[0] if len(models) == 1 else models,
                'params': cfg['params'],
                'installed': all(m in installed for m in models),
            })
        return Response({
            'tier': setting.model_tier,
            'model': settings.MODEL_TIERS[setting.model_tier]['llm_model'],
            'available': available,
            'pipeline': self._pipeline_map(setting),
        })

    def patch(self, request):
        payload = request.data.get('pipeline')
        if not isinstance(payload, dict):
            return Response(
                {'detail': 'pipeline must be an object mapping step -> enabled boolean'},
                status=400,
            )
        invalid = [key for key in payload if key not in PIPELINE_STEPS]
        if invalid:
            return Response(
                {'detail': f'Unknown pipeline steps: {", ".join(invalid)}'},
                status=400,
            )
        disabled = [step for step, enabled in payload.items() if not enabled]
        setting = PlatformSetting.get_solo()
        setting.disabled_pipeline_steps = disabled
        setting.save(update_fields=['disabled_pipeline_steps', 'updated_at'])
        return Response({
            'detail': 'Pipeline settings saved',
            'pipeline': self._pipeline_map(setting),
        })

    def put(self, request):
        serializer = ModelSettingsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_tier = serializer.validated_data['tier']
        cfg = settings.MODEL_TIERS[new_tier]
        models = list(dict.fromkeys([cfg['llm_model'], cfg['rca_model']]))
        try:
            for model in models:
                self._ensure_usable(model)
        except Exception as exc:
            return Response(
                {
                    'detail': str(exc),
                    'tier': PlatformSetting.get_solo().model_tier,
                },
                status=502,
            )
        setting = PlatformSetting.get_solo()
        setting.model_tier = new_tier
        setting.save(update_fields=['model_tier', 'updated_at'])
        return Response({
            'detail': 'Model profile saved and verified',
            'tier': new_tier,
            'model': cfg['llm_model'],
        })
