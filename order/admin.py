from django.contrib import admin
from order.models import Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "product", "quantity", "created_at")
    list_filter = ("created_at",)
