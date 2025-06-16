from django.contrib.auth.models import User
from rest_framework import serializers

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


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name"]
        read_only_fields = ["id"]


class FamilySerializer(serializers.ModelSerializer):
    members_count = serializers.SerializerMethodField()

    class Meta:
        model = Family
        fields = ["id", "name", "created_at", "updated_at", "members_count"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_members_count(self, obj):
        return obj.familymember_set.count()


class FamilyMemberSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    family = FamilySerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True)
    family_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = FamilyMember
        fields = ["id", "user", "family", "role", "joined_at", "user_id", "family_id"]
        read_only_fields = ["id", "joined_at"]


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ["id", "name", "description", "created_at"]
        read_only_fields = ["id", "created_at"]


class RecipeIngredientSerializer(serializers.ModelSerializer):
    ingredient = IngredientSerializer(read_only=True)
    ingredient_id = serializers.IntegerField(write_only=True)
    cuisine_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = RecipeIngredient
        fields = [
            "id", "ingredient", "quantity", "unit", "is_optional",
            "is_substitutable", "ingredient_id", "cuisine_id"
        ]
        read_only_fields = ["id"]


class CuisineSerializer(serializers.ModelSerializer):
    recipe_ingredients = RecipeIngredientSerializer(many=True, read_only=True)
    created_by = UserSerializer(read_only=True)
    family = FamilySerializer(read_only=True)
    family_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Cuisine
        fields = [
            "id",
            "name",
            "description",
            "default_time_min",
            "created_by",
            "family",
            "created_at",
            "updated_at",
            "recipe_ingredients",
            "family_id",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "created_by"]

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)


class MenuCuisineSerializer(serializers.ModelSerializer):
    """Serializer for menu display with availability information"""

    recipe_ingredients = RecipeIngredientSerializer(many=True, read_only=True)
    created_by = UserSerializer(read_only=True)
    is_available = serializers.SerializerMethodField()

    class Meta:
        model = Cuisine
        fields = [
            "id",
            "name",
            "description",
            "default_time_min",
            "created_by",
            "created_at",
            "updated_at",
            "recipe_ingredients",
            "is_available",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "created_by"]

    def get_is_available(self, obj):
        return obj.is_available()


class PantryStockSerializer(serializers.ModelSerializer):
    ingredient = IngredientSerializer(read_only=True)
    family = FamilySerializer(read_only=True)
    ingredient_id = serializers.IntegerField(write_only=True)
    family_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = PantryStock
        fields = [
            "id",
            "family",
            "ingredient",
            "qty_available",
            "unit",
            "best_before",
            "created_at",
            "updated_at",
            "family_id",
            "ingredient_id",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class OrderItemIngredientSerializer(serializers.ModelSerializer):
    ingredient = IngredientSerializer(read_only=True)
    ingredient_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = OrderItemIngredient
        fields = ["id", "ingredient", "quantity", "unit", "ingredient_id"]
        read_only_fields = ["id"]


class OrderSerializer(serializers.ModelSerializer):
    order_ingredients = OrderItemIngredientSerializer(many=True, read_only=True)
    created_by = UserSerializer(read_only=True)
    family = FamilySerializer(read_only=True)
    cuisine = CuisineSerializer(read_only=True)
    family_id = serializers.IntegerField(write_only=True)
    cuisine_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "family",
            "cuisine",
            "created_by",
            "status",
            "scheduled_for",
            "created_at",
            "updated_at",
            "order_ingredients",
            "family_id",
            "cuisine_id",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "created_by"]

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)


class AlertSerializer(serializers.ModelSerializer):
    ingredient = IngredientSerializer(read_only=True)
    family = FamilySerializer(read_only=True)

    class Meta:
        model = Alert
        fields = [
            "id",
            "family",
            "ingredient",
            "alert_type",
            "message",
            "is_resolved",
            "created_at",
            "resolved_at",
        ]
        read_only_fields = ["id", "created_at", "resolved_at"]


class LowStockThresholdSerializer(serializers.ModelSerializer):
    ingredient = IngredientSerializer(read_only=True)
    family = FamilySerializer(read_only=True)
    ingredient_id = serializers.IntegerField(write_only=True)
    family_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = LowStockThreshold
        fields = [
            "id",
            "family",
            "ingredient",
            "threshold_qty",
            "unit",
            "created_at",
            "updated_at",
            "family_id",
            "ingredient_id",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ShoppingListSerializer(serializers.ModelSerializer):
    ingredient = IngredientSerializer(read_only=True)
    family = FamilySerializer(read_only=True)
    ingredient_id = serializers.IntegerField(write_only=True)
    family_id = serializers.IntegerField(write_only=True)
    is_resolved = serializers.ReadOnlyField()

    class Meta:
        model = ShoppingList
        fields = [
            "id",
            "family",
            "ingredient",
            "qty_needed",
            "unit",
            "created_at",
            "resolved_at",
            "is_resolved",
            "family_id",
            "ingredient_id",
        ]
        read_only_fields = ["id", "created_at", "resolved_at"]
