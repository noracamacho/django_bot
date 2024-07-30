# paths/models.py
from django.db import models

class Path(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='Path Name')
    duration_weeks = models.IntegerField(verbose_name='Duration (weeks)')

    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'paths'

