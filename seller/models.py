from django.db import models
from users.models import User

class Shop(models.Model):
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="shops")
    legal_info = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

