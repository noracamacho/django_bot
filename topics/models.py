# topics/models.py
from django.db import models
from paths.models import Path

class Topic(models.Model):
    title = models.CharField(max_length=200, verbose_name='Topic Title')
    description = models.TextField(verbose_name='Description', blank=True, null=True)
    week = models.IntegerField(verbose_name='Week')
    path = models.ForeignKey(Path, on_delete=models.CASCADE, related_name='topics')

    def __str__(self):
        return self.title
    
    class Meta:
        db_table = 'topics'
