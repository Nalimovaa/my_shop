from rest_framework import viewsets
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiExample
from users.permissions import IsCustomAuthenticated, RolePermission
from .models import Product
from .serializers import ProductSerializer


class ProductViewSet(viewsets.ModelViewSet):
    """ CRUD for products.
    Checking permissions via RolePermission """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsCustomAuthenticated, RolePermission]
    business_element = "Product"

    @extend_schema(
        summary="Создать продукт",
        description="Создает новый продукт и автоматически привязывает его к текущему пользователю",
        request=ProductSerializer,
        responses={
            201: ProductSerializer,
            400: OpenApiExample("Bad Request", value={"detail": "Invalid data"}),
            401: OpenApiExample("Unauthorized", value={"detail": "User not authenticated"}),
            403: OpenApiExample("Forbidden", value={"detail": "You do not have permission to create product"}),
        }
    )
    def create(self, request, *args, **kwargs):
        """Product creation"""
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @extend_schema(
        summary="Список продуктов",
        description="Возвращает все продукты, доступные пользователю",
        responses={
            200: ProductSerializer,
            401: OpenApiExample("Unauthorized", value={"detail": "User not authenticated"}),
            403: OpenApiExample("Forbidden", value={"detail": "You do not have permission to view products"}),
        }
    )
    def list(self, request, *args, **kwargs):
        """List of all products"""
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Получить продукт",
        description="Возвращает продукт по ID",
        responses={
            200: ProductSerializer,
            401: OpenApiExample("Unauthorized", value={"detail": "User not authenticated"}),
            403: OpenApiExample("Forbidden", value={"detail": "You do not have permission to view this product"}),
            404: OpenApiExample("Not Found", value={"detail": "Product not found"}),
        }
    )
    def retrieve(self, request, *args, **kwargs):
        """Get product by ID"""
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Частично обновить продукт",
        description="Частично обновляет продукт",
        request=ProductSerializer,
        responses={
            200: ProductSerializer,
            401: OpenApiExample("Unauthorized", value={"detail": "User not authenticated"}),
            403: OpenApiExample("Forbidden", value={"detail": "You do not have permission to update this product"}),
            404: OpenApiExample("Not Found", value={"detail": "Product not found"}),
        }
    )
    def partial_update(self, request, *args, **kwargs):
        """Partial update"""
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        summary="Удалить продукт",
        description="Удаляет продукт по ID",
        responses={
            204: OpenApiExample("Deleted", value={"detail": "Product deleted"}),
            401: OpenApiExample("Unauthorized", value={"detail": "User not authenticated"}),
            403: OpenApiExample("Forbidden", value={"detail": "You do not have permission to delete this product"}),
            404: OpenApiExample("Not Found", value={"detail": "Product not found"}),
        }
    )
    def destroy(self, request, *args, **kwargs):
        """Removing the product"""
        return super().destroy(request, *args, **kwargs)
