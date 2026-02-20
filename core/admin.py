from django.contrib import admin
from core.models import BusinessElement, AccessRolesRules


@admin.register(BusinessElement)
class BusinessElementAdmin(admin.ModelAdmin):
    list_display = ("name",)


@admin.register(AccessRolesRules)
class AccessRolesRulesAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "role",
        "element",
        "read_permission",
        "read_all_permission",
        "create_permission",
        "update_permission",
        "update_all_permission",
        "delete_permission",
        "delete_all_permission",
    )
    list_filter = ("role", "element")
    search_fields = ("role__name", "element__name")


