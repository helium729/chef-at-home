from django.contrib.auth.models import User
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Cuisine, Family, FamilyMember, Ingredient, PantryStock, RecipeIngredient
from .serializers import (
    CuisineSerializer,
    FamilyMemberSerializer,
    FamilySerializer,
    IngredientSerializer,
    PantryStockSerializer,
    RecipeIngredientSerializer,
    UserSerializer,
)


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
