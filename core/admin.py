from django.contrib import admin

from .models import (
    Alert,
    Cuisine,
    Family,
    FamilyMember,
    Ingredient,
    LowStockThreshold,
    Order,
    PantryStock,
    RecipeIngredient,
    ShoppingList,
)


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


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["id", "family", "cuisine", "created_by", "status", "created_at"]
    list_filter = ["status", "family", "created_at"]
    search_fields = ["cuisine__name", "family__name", "created_by__username"]


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ["family", "ingredient", "alert_type", "is_resolved", "created_at"]
    list_filter = ["alert_type", "is_resolved", "family"]
    search_fields = ["family__name", "ingredient__name"]
    actions = ["mark_resolved"]

    def mark_resolved(self, request, queryset):
        from django.utils import timezone

        queryset.update(is_resolved=True, resolved_at=timezone.now())

    mark_resolved.short_description = "Mark selected alerts as resolved"


@admin.register(LowStockThreshold)
class LowStockThresholdAdmin(admin.ModelAdmin):
    list_display = ["family", "ingredient", "threshold_qty", "unit", "updated_at"]
    list_filter = ["family", "unit"]
    search_fields = ["family__name", "ingredient__name"]


@admin.register(ShoppingList)
class ShoppingListAdmin(admin.ModelAdmin):
    list_display = ["family", "ingredient", "qty_needed", "unit", "is_resolved", "created_at"]
    list_filter = ["family", "unit", "resolved_at"]
    search_fields = ["family__name", "ingredient__name"]
    actions = ["mark_resolved"]

    def is_resolved(self, obj):
        return obj.is_resolved

    is_resolved.boolean = True
    is_resolved.short_description = "Resolved"

    def mark_resolved(self, request, queryset):
        from django.utils import timezone

        queryset.update(resolved_at=timezone.now())

    mark_resolved.short_description = "Mark selected items as resolved"
