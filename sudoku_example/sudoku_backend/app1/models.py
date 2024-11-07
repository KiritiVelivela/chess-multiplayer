from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Board(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    location = models.CharField(max_length=4)
    value = models.SmallIntegerField()
    class Meta:
	       unique_together = ("user", "location")
