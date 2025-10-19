from rest_framework import serializers
from task.models import Task, SubTask
from accounts.serilaizers import CustomUserSerializer
from django.utils.translation import gettext_lazy as _


class TaskSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer(read_only=True)

    class Meta:
        model = Task
        fields = ['id', 'user', 'title', 'description', 'deadline', 'completed', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']

    def create(self, validated_data):
        user = self.context['request'].user
        if not user.is_authenticated:
            raise serializers.ValidationError({"detail": _("Authentication required.")})
        
        # إزالة أي user جاي من البيانات عشان مايحصلش conflict
        validated_data.pop('user', None)

        task = Task.objects.create(user=user, **validated_data)
        return task

    def update(self, instance, validated_data):
        instance.title = validated_data.get('title', instance.title)
        instance.description = validated_data.get('description', instance.description)
        instance.completed = validated_data.get('completed', instance.completed)
        instance.save()
        return instance


class SubTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubTask
        fields = ['id', 'task', 'title', 'completed', 'created_at']
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        user = self.context['request'].user
        if not user.is_authenticated:
            raise serializers.ValidationError({"detail": _("Authentication required.")})
        
        task = validated_data.get('task')
        if task.user != user:
            raise serializers.ValidationError({"detail": _("You do not have permission to add a subtask to this task.")})
        
        subtask = SubTask.objects.create(**validated_data)
        return subtask
