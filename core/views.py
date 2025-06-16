from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import (
    Alert,
    Cuisine,
    Family,
    FamilyMember,
    Ingredient,
    LowStockThreshold,
    Order,
    OrderItemIngredient,
    PantryStock,
    RecipeIngredient,
    ShoppingList,
)
from .serializers import (
    AlertSerializer,
    CuisineSerializer,
    FamilyMemberSerializer,
    FamilySerializer,
    IngredientSerializer,
    LowStockThresholdSerializer,
    MenuCuisineSerializer,
    OrderSerializer,
    PantryStockSerializer,
    RecipeIngredientSerializer,
    ShoppingListSerializer,
    UserSerializer,
)
from .utils import send_order_update


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing user information
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Users can only see other users in their families
        user_families = FamilyMember.objects.filter(user=self.request.user).values_list("family", flat=True)
        family_user_ids = FamilyMember.objects.filter(family__in=user_families).values_list("user", flat=True)
        return User.objects.filter(id__in=family_user_ids)


class FamilyViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing families
    """

    queryset = Family.objects.all()
    serializer_class = FamilySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Users can only see families they belong to
        return Family.objects.filter(familymember__user=self.request.user)


class FamilyMemberViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing family memberships
    """

    queryset = FamilyMember.objects.all()
    serializer_class = FamilyMemberSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Users can only see memberships in their families
        user_families = FamilyMember.objects.filter(user=self.request.user).values_list("family", flat=True)
        return FamilyMember.objects.filter(family__in=user_families)


class IngredientViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing ingredients
    """

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [permissions.IsAuthenticated]


class CuisineViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing cuisines/recipes
    """

    queryset = Cuisine.objects.all()
    serializer_class = CuisineSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Users can only see cuisines from their families
        user_families = FamilyMember.objects.filter(user=self.request.user).values_list("family", flat=True)
        return Cuisine.objects.filter(family__in=user_families)

    @action(detail=True, methods=["get"])
    def ingredients(self, request, pk=None):
        """Get ingredients for a specific cuisine"""
        cuisine = self.get_object()
        recipe_ingredients = RecipeIngredient.objects.filter(cuisine=cuisine)
        serializer = RecipeIngredientSerializer(recipe_ingredients, many=True)
        return Response(serializer.data)


class RecipeIngredientViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing recipe ingredients
    """

    queryset = RecipeIngredient.objects.all()
    serializer_class = RecipeIngredientSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Users can only see recipe ingredients from their families' cuisines
        user_families = FamilyMember.objects.filter(user=self.request.user).values_list("family", flat=True)
        return RecipeIngredient.objects.filter(cuisine__family__in=user_families)


class PantryStockViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing pantry stock
    """

    queryset = PantryStock.objects.all()
    serializer_class = PantryStockSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Users can only see pantry stock from their families
        user_families = FamilyMember.objects.filter(user=self.request.user).values_list("family", flat=True)
        return PantryStock.objects.filter(family__in=user_families)


class MenuViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing menu with availability information
    """

    queryset = Cuisine.objects.all()
    serializer_class = MenuCuisineSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Users can only see cuisines from their families
        user_families = FamilyMember.objects.filter(user=self.request.user).values_list("family", flat=True)
        return Cuisine.objects.filter(family__in=user_families)


class OrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing orders
    """

    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Users can only see orders from their families
        user_families = FamilyMember.objects.filter(user=self.request.user).values_list("family", flat=True)
        return Order.objects.filter(family__in=user_families)

    def perform_create(self, serializer):
        # Create order and automatically create OrderItemIngredient snapshots
        order = serializer.save()

        # Create ingredient snapshots from the cuisine recipe
        for recipe_ingredient in order.cuisine.recipe_ingredients.all():
            OrderItemIngredient.objects.create(
                order=order,
                ingredient=recipe_ingredient.ingredient,
                quantity=recipe_ingredient.quantity,
                unit=recipe_ingredient.unit,
            )

        # Send WebSocket notification
        order_data = OrderSerializer(order, context={"request": self.request}).data
        send_order_update(order.family.id, order_data)

    @action(detail=True, methods=["patch"])
    def update_status(self, request, pk=None):
        """Update order status"""
        order = self.get_object()
        new_status = request.data.get("status")

        if new_status not in dict(Order.STATUS_CHOICES):
            return Response({"error": "Invalid status"}, status=400)

        order.status = new_status
        order.save()

        # If status is DONE, deduct ingredients from pantry
        if new_status == "DONE":
            self._deduct_ingredients_from_pantry(order)

        # Send WebSocket notification
        serializer = self.get_serializer(order)
        send_order_update(order.family.id, serializer.data)

        return Response(serializer.data)

    def _deduct_ingredients_from_pantry(self, order):
        """Deduct used ingredients from pantry when order is completed"""
        for order_ingredient in order.order_ingredients.all():
            try:
                pantry_stock = PantryStock.objects.get(family=order.family, ingredient=order_ingredient.ingredient)

                # Deduct the used quantity
                pantry_stock.qty_available -= order_ingredient.quantity

                # Ensure we don't go negative
                if pantry_stock.qty_available < 0:
                    pantry_stock.qty_available = 0

                pantry_stock.save()

            except PantryStock.DoesNotExist:
                # If ingredient doesn't exist in pantry, skip
                continue


class AlertViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing alerts
    """

    queryset = Alert.objects.all()
    serializer_class = AlertSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Users can only see alerts from their families
        user_families = FamilyMember.objects.filter(user=self.request.user).values_list("family", flat=True)
        return Alert.objects.filter(family__in=user_families)

    @action(detail=True, methods=["patch"])
    def resolve(self, request, pk=None):
        """Mark an alert as resolved"""
        alert = self.get_object()
        alert.is_resolved = True
        alert.resolved_at = timezone.now()
        alert.save()

        serializer = self.get_serializer(alert)
        return Response(serializer.data)


class LowStockThresholdViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing low stock thresholds
    """

    queryset = LowStockThreshold.objects.all()
    serializer_class = LowStockThresholdSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Users can only see thresholds from their families
        user_families = FamilyMember.objects.filter(user=self.request.user).values_list("family", flat=True)
        return LowStockThreshold.objects.filter(family__in=user_families)


class ShoppingListViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing shopping list items
    """

    queryset = ShoppingList.objects.all()
    serializer_class = ShoppingListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Users can only see shopping list items from their families
        user_families = FamilyMember.objects.filter(user=self.request.user).values_list("family", flat=True)
        return ShoppingList.objects.filter(family__in=user_families)

    @action(detail=True, methods=["patch"])
    def resolve(self, request, pk=None):
        """Mark a shopping list item as resolved"""
        shopping_item = self.get_object()
        shopping_item.resolved_at = timezone.now()
        shopping_item.save()

        serializer = self.get_serializer(shopping_item)
        
        # Send WebSocket notification
        from .utils import send_shopping_list_update
        send_shopping_list_update(shopping_item.family.id, serializer.data)
        
        return Response(serializer.data)
