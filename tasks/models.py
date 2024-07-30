# tasks/modules.py
from django.db import models
from topics.models import Topic

class Task(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    topic = models.ForeignKey(Topic, related_name='tasks', on_delete=models.CASCADE)
    
    def __str__(self):
        return self.title
    
    class Meta:
        db_table = 'tasks'