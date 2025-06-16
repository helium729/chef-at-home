import json
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Cuisine, Family, FamilyMember, Ingredient, Order, OrderItemIngredient, PantryStock, RecipeIngredient


class HealthCheckTests(TestCase):
    """Test the API health check endpoint"""

    def setUp(self):
        self.client = Client()

    def test_health_check_endpoint(self):
        """Test that the health check endpoint returns expected response"""
        response = self.client.get("/api/health/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")

        data = json.loads(response.content)
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["message"], "FamilyChef API is running")
        self.assertEqual(data["version"], "1.0.0")


class ModelTests(TestCase):
    """Test the core models"""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="testpass123")
        self.family = Family.objects.create(name="Test Family")
        self.ingredient = Ingredient.objects.create(name="Tomato", description="Fresh red tomato")

    def test_family_creation(self):
        """Test family model creation"""
        self.assertEqual(self.family.name, "Test Family")
        self.assertEqual(str(self.family), "Test Family")

    def test_family_member_creation(self):
        """Test family member relationship"""
        member = FamilyMember.objects.create(user=self.user, family=self.family, role="chef")
        self.assertEqual(member.user, self.user)
        self.assertEqual(member.family, self.family)
        self.assertEqual(member.role, "chef")
        self.assertEqual(str(member), "testuser - Test Family (chef)")

    def test_ingredient_creation(self):
        """Test ingredient model creation"""
        self.assertEqual(self.ingredient.name, "Tomato")
        self.assertEqual(self.ingredient.description, "Fresh red tomato")
        self.assertEqual(str(self.ingredient), "Tomato")

    def test_cuisine_creation(self):
        """Test cuisine model creation"""
        cuisine = Cuisine.objects.create(
            name="Tomato Pasta",
            description="Delicious tomato pasta",
            default_time_min=30,
            created_by=self.user,
            family=self.family,
        )
        self.assertEqual(cuisine.name, "Tomato Pasta")
        self.assertEqual(cuisine.default_time_min, 30)
        self.assertEqual(cuisine.created_by, self.user)
        self.assertEqual(cuisine.family, self.family)
        self.assertEqual(str(cuisine), "Tomato Pasta (Test Family)")

    def test_recipe_ingredient_creation(self):
        """Test recipe ingredient relationship"""
        cuisine = Cuisine.objects.create(
            name="Tomato Salad", default_time_min=10, created_by=self.user, family=self.family
        )
        recipe_ingredient = RecipeIngredient.objects.create(
            cuisine=cuisine,
            ingredient=self.ingredient,
            quantity=Decimal("2.5"),
            unit="pieces",
            is_optional=False,
            is_substitutable=True,
        )
        self.assertEqual(recipe_ingredient.cuisine, cuisine)
        self.assertEqual(recipe_ingredient.ingredient, self.ingredient)
        self.assertEqual(recipe_ingredient.quantity, Decimal("2.5"))
        self.assertEqual(recipe_ingredient.unit, "pieces")
        self.assertFalse(recipe_ingredient.is_optional)
        self.assertTrue(recipe_ingredient.is_substitutable)

    def test_pantry_stock_creation(self):
        """Test pantry stock model creation"""
        stock = PantryStock.objects.create(
            family=self.family,
            ingredient=self.ingredient,
            qty_available=Decimal("10.0"),
            unit="pieces",
            best_before=date.today() + timedelta(days=7),
        )
        self.assertEqual(stock.family, self.family)
        self.assertEqual(stock.ingredient, self.ingredient)
        self.assertEqual(stock.qty_available, Decimal("10.0"))
        self.assertEqual(stock.unit, "pieces")


class APITests(APITestCase):
    """Test the REST API endpoints"""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="testpass123")
        self.other_user = User.objects.create_user(
            username="otheruser", email="other@example.com", password="testpass123"
        )
        self.family = Family.objects.create(name="Test Family")
        self.other_family = Family.objects.create(name="Other Family")

        # Add user to family
        FamilyMember.objects.create(user=self.user, family=self.family, role="chef")
        # Add other user to other family
        FamilyMember.objects.create(user=self.other_user, family=self.other_family, role="member")

        self.ingredient = Ingredient.objects.create(name="Test Ingredient", description="A test ingredient")

    def test_authentication_required(self):
        """Test that authentication is required for API endpoints"""
        response = self.client.get("/api/families/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_family_list_api(self):
        """Test family list API with authentication"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/families/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        # Handle pagination
        if "results" in data:
            families = data["results"]
        else:
            families = data

        self.assertEqual(len(families), 1)  # User should only see their own family
        self.assertEqual(families[0]["name"], "Test Family")

    def test_family_isolation(self):
        """Test that users can only see their own families"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/families/")
        data = response.json()

        # Handle pagination
        if "results" in data:
            families = data["results"]
        else:
            families = data

        family_names = [f["name"] for f in families]

        self.assertIn("Test Family", family_names)
        self.assertNotIn("Other Family", family_names)

    def test_ingredient_crud(self):
        """Test ingredient CRUD operations"""
        self.client.force_authenticate(user=self.user)

        # Test create
        data = {"name": "New Ingredient", "description": "A new test ingredient"}
        response = self.client.post("/api/ingredients/", data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Test read
        response = self.client.get("/api/ingredients/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        # Handle pagination
        if "results" in data:
            ingredients = data["results"]
        else:
            ingredients = data

        self.assertTrue(len(ingredients) >= 2)  # At least our test ingredient and new one

        # Test update
        ingredient_id = ingredients[0]["id"]
        update_data = {"name": "Updated Ingredient", "description": "Updated description"}
        response = self.client.patch(f"/api/ingredients/{ingredient_id}/", update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Test delete
        response = self.client.delete(f"/api/ingredients/{ingredient_id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_cuisine_creation(self):
        """Test cuisine creation through API"""
        self.client.force_authenticate(user=self.user)

        data = {
            "name": "Test Cuisine",
            "description": "A test cuisine",
            "default_time_min": 25,
            "family_id": self.family.id,
        }
        response = self.client.post("/api/cuisines/", data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        cuisine_data = response.json()
        self.assertEqual(cuisine_data["name"], "Test Cuisine")
        self.assertEqual(cuisine_data["default_time_min"], 25)
        self.assertEqual(cuisine_data["created_by"]["username"], "testuser")

    def test_pantry_stock_operations(self):
        """Test pantry stock operations"""
        self.client.force_authenticate(user=self.user)

        data = {
            "family_id": self.family.id,
            "ingredient_id": self.ingredient.id,
            "qty_available": "15.5",
            "unit": "kg",
            "best_before": (date.today() + timedelta(days=14)).isoformat(),
        }
        response = self.client.post("/api/pantry-stock/", data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        stock_data = response.json()
        self.assertEqual(float(stock_data["qty_available"]), 15.5)
        self.assertEqual(stock_data["unit"], "kg")

    def test_menu_availability(self):
        """Test menu endpoint shows availability information"""
        self.client.force_authenticate(user=self.user)
        
        # Create a cuisine with ingredients
        cuisine = Cuisine.objects.create(
            name="Test Dish",
            description="A test dish",
            default_time_min=30,
            created_by=self.user,
            family=self.family,
        )
        
        # Add ingredient requirement
        RecipeIngredient.objects.create(
            cuisine=cuisine,
            ingredient=self.ingredient,
            quantity=Decimal("2.0"),
            unit="pieces",
            is_optional=False,
        )
        
        # Test without stock - should be unavailable
        response = self.client.get("/api/menu/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        if "results" in data:
            menu_items = data["results"]
        else:
            menu_items = data
            
        dish = next((item for item in menu_items if item["name"] == "Test Dish"), None)
        self.assertIsNotNone(dish)
        self.assertFalse(dish["is_available"])
        
        # Add sufficient stock
        PantryStock.objects.create(
            family=self.family,
            ingredient=self.ingredient,
            qty_available=Decimal("5.0"),
            unit="pieces",
        )
        
        # Test with stock - should be available
        response = self.client.get("/api/menu/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        if "results" in data:
            menu_items = data["results"]
        else:
            menu_items = data
            
        dish = next((item for item in menu_items if item["name"] == "Test Dish"), None)
        self.assertIsNotNone(dish)
        self.assertTrue(dish["is_available"])

    def test_order_creation(self):
        """Test order creation"""
        self.client.force_authenticate(user=self.user)
        
        # Create a cuisine
        cuisine = Cuisine.objects.create(
            name="Test Order Dish",
            description="A test dish for ordering",
            default_time_min=45,
            created_by=self.user,
            family=self.family,
        )
        
        # Add ingredient to the cuisine
        RecipeIngredient.objects.create(
            cuisine=cuisine,
            ingredient=self.ingredient,
            quantity=Decimal("3.0"),
            unit="pieces",
        )
        
        # Create order
        data = {
            "family_id": self.family.id,
            "cuisine_id": cuisine.id,
            "scheduled_for": (timezone.now() + timedelta(hours=2)).isoformat(),
        }
        response = self.client.post("/api/orders/", data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        order_data = response.json()
        self.assertEqual(order_data["status"], "NEW")
        self.assertEqual(order_data["cuisine"]["name"], "Test Order Dish")
        self.assertEqual(order_data["created_by"]["username"], "testuser")
        
        # Check that OrderItemIngredient was created
        order_id = order_data["id"]
        order = Order.objects.get(id=order_id)
        self.assertEqual(order.order_ingredients.count(), 1)
        
        order_ingredient = order.order_ingredients.first()
        self.assertEqual(order_ingredient.ingredient, self.ingredient)
        self.assertEqual(order_ingredient.quantity, Decimal("3.0"))
        self.assertEqual(order_ingredient.unit, "pieces")

    def test_order_status_update(self):
        """Test order status update"""
        self.client.force_authenticate(user=self.user)
        
        # Create cuisine and order
        cuisine = Cuisine.objects.create(
            name="Status Test Dish",
            default_time_min=20,
            created_by=self.user,
            family=self.family,
        )
        
        order = Order.objects.create(
            family=self.family,
            cuisine=cuisine,
            created_by=self.user,
            status="NEW",
        )
        
        # Update status to COOKING
        data = {"status": "COOKING"}
        response = self.client.patch(f"/api/orders/{order.id}/update_status/", data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        order_data = response.json()
        self.assertEqual(order_data["status"], "COOKING")
        
        # Verify in database
        order.refresh_from_db()
        self.assertEqual(order.status, "COOKING")
        
        # Test invalid status
        data = {"status": "INVALID"}
        response = self.client.patch(f"/api/orders/{order.id}/update_status/", data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_ingredient_deduction_on_order_completion(self):
        """Test that ingredients are deducted from pantry when order is marked as DONE"""
        self.client.force_authenticate(user=self.user)
        
        # Create cuisine with ingredients
        cuisine = Cuisine.objects.create(
            name="Deduction Test Dish",
            default_time_min=25,
            created_by=self.user,
            family=self.family,
        )
        
        # Add ingredient to cuisine
        RecipeIngredient.objects.create(
            cuisine=cuisine,
            ingredient=self.ingredient,
            quantity=Decimal("3.0"),
            unit="pieces",
        )
        
        # Add stock to pantry
        pantry_stock = PantryStock.objects.create(
            family=self.family,
            ingredient=self.ingredient,
            qty_available=Decimal("10.0"),
            unit="pieces",
        )
        
        # Create order
        order = Order.objects.create(
            family=self.family,
            cuisine=cuisine,
            created_by=self.user,
            status="NEW",
        )
        
        # Create order ingredient (this would normally be done automatically)
        OrderItemIngredient.objects.create(
            order=order,
            ingredient=self.ingredient,
            quantity=Decimal("3.0"),
            unit="pieces",
        )
        
        # Mark order as DONE
        data = {"status": "DONE"}
        response = self.client.patch(f"/api/orders/{order.id}/update_status/", data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that ingredients were deducted
        pantry_stock.refresh_from_db()
        self.assertEqual(pantry_stock.qty_available, Decimal("7.0"))  # 10 - 3 = 7
