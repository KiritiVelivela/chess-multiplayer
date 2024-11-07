from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class JournalEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    datetime = models.DateField(auto_now=True)
    description = models.CharField(max_length=128)
    entry = models.CharField(max_length=65536)
