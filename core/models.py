from django.db import models
from users.models import Role

class BusinessElement(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class AccessRolesRules(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="access_rules")
    element = models.ForeignKey(BusinessElement, on_delete=models.CASCADE, related_name="access_rules")

    # Viewing own object
    read_permission = models.BooleanField(default=False)
    # View all objects
    read_all_permission = models.BooleanField(default=False)
    # Creating objects
    create_permission = models.BooleanField(default=False)
    # Editing own object
    update_permission = models.BooleanField(default=False)
    # Editing all objects
    update_all_permission = models.BooleanField(default=False)
    # Deleting own object
    delete_permission = models.BooleanField(default=False)
    # Deleting all objects
    delete_all_permission = models.BooleanField(default=False)

    def __str__(self):
        return f"AccessRule: {self.role} → {self.element}"

