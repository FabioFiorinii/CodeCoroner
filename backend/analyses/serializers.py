from rest_framework import serializers

from repositories.models import Repository

from .models import (
    Analysis,
    AnalysisRun,
    BugLocalization,
    FixSuggestion,
    Patch,
    PatchValidation,
    Report,
    RootCause,
    SuspiciousFileScore,
)


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
        fields = [
            'summary',
            'root_file',
            'root_line',
            'cause_chain',
            'confidence',
            'reasoning',
            'created_at',
        ]


class PatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patch
        fields = ['id', 'diff', 'summary', 'status', 'created_at']
        read_only_fields = ['id', 'status', 'created_at']


class PatchValidationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatchValidation
        fields = [
            'tests_passed',
            'tests_failed',
            'tests_skipped',
            'lint_errors',
            'lint_warnings',
            'type_errors',
            'overall_score',
            'output_log',
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
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    children_count = serializers.IntegerField(read_only=True, default=0)
    latest_status = serializers.CharField(read_only=True, allow_blank=True)
    latest_error_message = serializers.CharField(read_only=True, allow_blank=True)

    class Meta:
        model = Analysis
        fields = [
            'id',
            'parent_analysis',
            'user',
            'user_email',
            'user_username',
            'project',
            'repository',
            'repositories',
            'title',
            'error_context',
            'status',
            'created_at',
            'completed_at',
            'duration_seconds',
            'error_message',
            'runs',
            'bug_localization',
            'root_cause',
            'patch',
            'fix_suggestion',
            'report',
            'children_count',
            'latest_status',
            'latest_error_message',
        ]
        read_only_fields = [
            'id',
            'parent_analysis',
            'user',
            'status',
            'created_at',
            'completed_at',
            'duration_seconds',
            'error_message',
            'runs',
            'bug_localization',
            'root_cause',
            'patch',
            'fix_suggestion',
            'report',
            'children_count',
            'latest_status',
            'latest_error_message',
        ]


class AnalysisCreateSerializer(serializers.ModelSerializer):
    parent_analysis = serializers.UUIDField(required=False, write_only=True)
    repository_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False,
    )

    class Meta:
        model = Analysis
        fields = [
            'project',
            'repository',
            'repository_ids',
            'title',
            'error_context',
            'parent_analysis',
        ]

    def validate_error_context(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError('error_context must be a JSON object')
        return value

    def validate_parent_analysis(self, value):
        parent = Analysis.objects.filter(id=value).first()
        if parent is None:
            raise serializers.ValidationError('Parent analysis not found.')
        project = self.initial_data.get('project')
        if project and str(parent.project_id) != str(project):
            raise serializers.ValidationError('Parent analysis must belong to the same project.')
        return parent

    def validate(self, attrs):
        repo_ids = set()
        repository = attrs.get('repository')
        if repository:
            repo_ids.add(repository.id)
        for rid in (attrs.get('repository_ids') or []):
            repo_ids.add(rid)
        if repo_ids:
            repos = Repository.objects.filter(id__in=repo_ids)
            for repo in repos:
                if repo.status != Repository.Status.INDEXED:
                    raise serializers.ValidationError(
                        f'Repository "{repo.git_url}" is not ready yet (status: {repo.status}). '
                        'Wait for indexing to complete before starting an analysis.'
                    )
        return attrs

    def create(self, validated_data):
        parent = validated_data.pop('parent_analysis', None)
        repo_ids = validated_data.pop('repository_ids', None)
        analysis = super().create(validated_data)
        if parent:
            root = parent.parent_analysis if parent.parent_analysis else parent
            analysis.parent_analysis = root
            analysis.save(update_fields=['parent_analysis'])
        if repo_ids:
            analysis.repositories.set(repo_ids)
        else:
            analysis.repositories.add(analysis.repository)
        return analysis
