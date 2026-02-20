from django.urls import path, include
from rest_framework.routers import DefaultRouter
from core.views import AdminRolesViewSet

router = DefaultRouter()
router.register(r'admin-roles', AdminRolesViewSet, basename='admin-roles')

urlpatterns = [
    path('', include(router.urls)),
]
