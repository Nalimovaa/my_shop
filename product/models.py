from django.db import models
from django.contrib.auth import get_user_model
from seller.models import Shop


User = get_user_model()


class Product(models.Model):
    name = models.CharField(max_length=255)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="products")
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="products")
    price = models.FloatField()

    def __str__(self):
        return self.name

