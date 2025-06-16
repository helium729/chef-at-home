from django.contrib import admin

from .models import Cuisine, Family, FamilyMember, Ingredient, PantryStock, RecipeIngredient


@admin.register(Family)
class FamilyAdmin(admin.ModelAdmin):
    list_display = ["name", "created_at"]
    search_fields = ["name"]


@admin.register(FamilyMember)
class FamilyMemberAdmin(admin.ModelAdmin):
    list_display = ["user", "family", "role", "joined_at"]
    list_filter = ["role", "family"]
    search_fields = ["user__username", "family__name"]


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ["name", "created_at"]
    search_fields = ["name"]


@admin.register(Cuisine)
class CuisineAdmin(admin.ModelAdmin):
    list_display = ["name", "family", "default_time_min", "created_by", "created_at"]
    list_filter = ["family", "created_by"]
    search_fields = ["name", "family__name"]


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ["cuisine", "ingredient", "quantity", "unit", "is_optional", "is_substitutable"]
    list_filter = ["is_optional", "is_substitutable", "unit"]
    search_fields = ["cuisine__name", "ingredient__name"]


@admin.register(PantryStock)
class PantryStockAdmin(admin.ModelAdmin):
    list_display = ["family", "ingredient", "qty_available", "unit", "best_before", "updated_at"]
    list_filter = ["family", "unit", "best_before"]
    search_fields = ["family__name", "ingredient__name"]
