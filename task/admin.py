from django.contrib import admin
from .models import Task, SubTask

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'user', 'completed', 'created_at')
    list_filter = ('completed', 'created_at')
    search_fields = ('title', 'description', 'user__email')
    ordering = ('-created_at',)

@admin.register(SubTask)
class SubTaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'task', 'completed', 'created_at')
    list_filter = ('completed', 'created_at')
    search_fields = ('title', 'task__title')
    ordering = ('-created_at',)
