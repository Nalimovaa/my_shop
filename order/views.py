from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiExample
from core.views import RBACListModelViewSet
from users.permissions import IsCustomAuthenticated, RolePermission
from .models import Order
from .serializers import OrderSerializer


class OrderViewSet(RBACListModelViewSet):
    """ CRUD для заказов.
    Проверка прав через RolePermission """
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsCustomAuthenticated, RolePermission]
    business_element = "Order"

    @extend_schema(
        summary="Создать заказ",
        description="Создает новый заказ и автоматически привязывает его к текущему пользователю",
        request=OrderSerializer,
        responses={
            201: OrderSerializer,
            400: OpenApiExample("Bad Request", value={"detail": "Invalid data"}),
            401: OpenApiExample("Unauthorized", value={"detail": "User not authenticated"}),
            403: OpenApiExample("Forbidden", value={"detail": "You do not have permission to create order"}),
        }
    )
    def create(self, request, *args, **kwargs):
        """Создание заказа"""
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @extend_schema(
        summary="Список заказов",
        description="Возвращает все заказы, доступные пользователю",
        responses={
            200: OrderSerializer,
            401: OpenApiExample("Unauthorized", value={"detail": "User not authenticated"}),
            403: OpenApiExample("Forbidden", value={"detail": "You do not have permission to view orders"}),
        }
    )
    def list(self, request, *args, **kwargs):
        """Список всех заказов"""
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Получить заказ",
        description="Возвращает заказ по ID",
        responses={
            200: OrderSerializer,
            401: OpenApiExample("Unauthorized", value={"detail": "User not authenticated"}),
            403: OpenApiExample("Forbidden", value={"detail": "You do not have permission to view this order"}),
            404: OpenApiExample("Not Found", value={"detail": "Order not found"}),
        }
    )
    def retrieve(self, request, *args, **kwargs):
        """Получить заказ по ID"""
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Частично обновить заказ",
        description="Частично обновляет заказ",
        request=OrderSerializer,
        responses={
            200: OrderSerializer,
            401: OpenApiExample("Unauthorized", value={"detail": "User not authenticated"}),
            403: OpenApiExample("Forbidden", value={"detail": "You do not have permission to update this order"}),
            404: OpenApiExample("Not Found", value={"detail": "Order not found"}),
        }
    )
    def partial_update(self, request, *args, **kwargs):
        """Частичное обновление заказа"""
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        summary="Удалить заказ",
        description="Удаляет заказ по ID",
        responses={
            204: OpenApiExample("Deleted", value={"detail": "Order deleted"}),
            401: OpenApiExample("Unauthorized", value={"detail": "User not authenticated"}),
            403: OpenApiExample("Forbidden", value={"detail": "You do not have permission to delete this order"}),
            404: OpenApiExample("Not Found", value={"detail": "Order not found"}),
        }
    )
    def destroy(self, request, *args, **kwargs):
        """Удаление заказа по ID"""
        return super().destroy(request, *args, **kwargs)

