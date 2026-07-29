from rest_framework import serializers
from django.contrib.auth.models import Group
from .models import Project, ProjectMembership

class ProjectMembershipSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = ProjectMembership
        fields = ['id', 'user', 'user_email', 'username', 'role', 'created_at']
        read_only_fields = ['id', 'created_at']

class ProjectSerializer(serializers.ModelSerializer):
    memberships = ProjectMembershipSerializer(many=True, read_only=True)
    member_count = serializers.SerializerMethodField()
    repo_count = serializers.SerializerMethodField()
    groups = serializers.SlugRelatedField(
        many=True, slug_field='name', queryset=Group.objects.all(), required=False,
    )

    class Meta:
        model = Project
        fields = [
            'id', 'name', 'description', 'created_by', 'created_at', 'updated_at',
            'memberships', 'member_count', 'repo_count', 'groups',
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def get_member_count(self, obj):
        return obj.memberships.count()

    def get_repo_count(self, obj):
        return obj.assigned_repositories.count()

    def create(self, validated_data):
        groups_data = validated_data.pop('groups', None)
        request = self.context.get('request')
        project = Project.objects.create(created_by=request.user, **validated_data)
        ProjectMembership.objects.create(
            project=project,
            user=request.user,
            role=ProjectMembership.Role.OWNER,
        )
        if groups_data is not None:
            project.groups.set(groups_data)
        else:
            project.groups.set(request.user.groups.all())
        return project
