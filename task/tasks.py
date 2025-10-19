

from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import Task
from django.core.mail import send_mail

@shared_task
def send_deadline_reminders():
    tomorrow = timezone.now() + timedelta(days=1)
    tasks = Task.objects.filter(deadline__date=tomorrow.date(), completed=False)

    for task in tasks:
        send_mail(
            subject=f"Reminder: Task '{task.title}' is due tomorrow",
            message=f"Your task '{task.title}' is due on {task.deadline.strftime('%Y-%m-%d %H:%M')}",
            from_email='noreply@todoapp.com',
            recipient_list=[task.user.email],
            fail_silently=True,
        )
