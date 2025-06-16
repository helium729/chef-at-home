from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"users", views.UserViewSet)
router.register(r"families", views.FamilyViewSet)
router.register(r"family-members", views.FamilyMemberViewSet)
router.register(r"ingredients", views.IngredientViewSet)
router.register(r"cuisines", views.CuisineViewSet)
router.register(r"recipe-ingredients", views.RecipeIngredientViewSet)
router.register(r"pantry-stock", views.PantryStockViewSet)
router.register(r"menu", views.MenuViewSet, basename="menu")
router.register(r"orders", views.OrderViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
