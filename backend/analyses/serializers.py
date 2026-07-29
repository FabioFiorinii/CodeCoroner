from rest_framework import serializers
from .models import (
    Analysis, AnalysisRun, BugLocalization, SuspiciousFileScore,
    RootCause, Patch, PatchValidation, Report, FixSuggestion,
)
from repositories.models import Repository


class RepositoryBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Repository
        fields = ['id', 'git_url', 'git_branch', 'status']

class SuspiciousFileScoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = SuspiciousFileScore
        fields = ['file_path', 'suspicion_score', 'matched_lines', 'evidence', 'rank']

class BugLocalizationSerializer(serializers.ModelSerializer):
    suspicious_files = SuspiciousFileScoreSerializer(many=True, read_only=True)

    class Meta:
        model = BugLocalization
        fields = ['summary', 'suspicious_files', 'created_at']

class RootCauseSerializer(serializers.ModelSerializer):
    class Meta:
        model = RootCause
        fields = ['summary', 'root_file', 'root_line', 'cause_chain', 'confidence', 'reasoning', 'created_at']

class PatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patch
        fields = ['id', 'diff', 'summary', 'status', 'created_at']
        read_only_fields = ['id', 'status', 'created_at']

class PatchValidationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatchValidation
        fields = [
            'tests_passed', 'tests_failed', 'tests_skipped',
            'lint_errors', 'lint_warnings', 'type_errors',
            'overall_score', 'output_log',
        ]

class FixSuggestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FixSuggestion
        fields = ['diff', 'plan', 'explanation', 'created_at']

class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = ['markdown', 'format', 'created_at']

class AnalysisRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalysisRun
        fields = ['id', 'step', 'status', 'started_at', 'completed_at', 'error', 'output']
        read_only_fields = ['id', 'started_at', 'completed_at']

class AnalysisSerializer(serializers.ModelSerializer):
    runs = AnalysisRunSerializer(many=True, read_only=True)
    bug_localization = BugLocalizationSerializer(read_only=True)
    root_cause = RootCauseSerializer(read_only=True)
    patch = PatchSerializer(read_only=True)
    fix_suggestion = FixSuggestionSerializer(read_only=True)
    report = ReportSerializer(read_only=True)
    repositories = RepositoryBasicSerializer(many=True, read_only=True)

    class Meta:
        model = Analysis
        fields = [
            'id', 'user', 'project', 'repository', 'repositories',
            'title', 'error_context',
            'status', 'created_at', 'completed_at', 'duration_seconds',
            'error_message', 'runs', 'bug_localization', 'root_cause',
            'patch', 'fix_suggestion', 'report',
        ]
        read_only_fields = [
            'id', 'user', 'status', 'created_at', 'completed_at',
            'duration_seconds', 'error_message', 'runs',
            'bug_localization', 'root_cause', 'patch', 'fix_suggestion', 'report',
        ]

class AnalysisCreateSerializer(serializers.ModelSerializer):
    repository_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False,
    )

    class Meta:
        model = Analysis
        fields = [
            'project', 'repository', 'repository_ids', 'title', 'error_context',
        ]

    def validate_error_context(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError('error_context must be a JSON object')
        return value

    def create(self, validated_data):
        repo_ids = validated_data.pop('repository_ids', None)
        analysis = super().create(validated_data)
        if repo_ids:
            analysis.repositories.set(repo_ids)
        else:
            analysis.repositories.add(analysis.repository)
        return analysis
