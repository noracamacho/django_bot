# topics/models.py
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
# from django.core.exceptions import ValidationError
from paths.models import Path

class Topic(models.Model):
    title = models.CharField(max_length=200, unique=True, verbose_name='Topic Title')
    description = models.TextField(verbose_name='Description', blank=True, null=True)
    week = models.IntegerField(verbose_name='Week', validators=[MinValueValidator(1), MaxValueValidator(52)])
    path = models.ForeignKey(Path, on_delete=models.CASCADE, related_name='topics')

    def __str__(self):
        return self.title
    
    class Meta:
        db_table = 'topics'
    
    # def clean(self):
    #     super().clean()
    #     if self.week < 1 or self.week > 52: 
    #         raise ValidationError({'week': 'Week must be between 1 and 52.'})
