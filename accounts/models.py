from django.db import models


# Create your models here.
from django.contrib.auth.models import User

class BurnoutRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date_created = models.DateTimeField(auto_now_add=True)
    risk_score = models.FloatField()
    status = models.CharField(max_length=50)
    sleep_hours = models.FloatField()
    strengths = models.TextField(blank=True, null=True) 
    risk_factors = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.status}({self.date_created.date()})"
