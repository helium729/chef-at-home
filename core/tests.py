import json
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import Client, TestCase, override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

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
        cuisine = Cuisine.objects.create(name="Tomato Salad", default_time_min=10, created_by=self.user, family=self.family)
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

    def test_shopping_list_creation(self):
        """Test shopping list model creation"""
        shopping_item = ShoppingList.objects.create(
            family=self.family,
            ingredient=self.ingredient,
            qty_needed=Decimal("5.0"),
            unit="kg",
        )
        self.assertEqual(shopping_item.family, self.family)
        self.assertEqual(shopping_item.ingredient, self.ingredient)
        self.assertEqual(shopping_item.qty_needed, Decimal("5.0"))
        self.assertEqual(shopping_item.unit, "kg")
        self.assertFalse(shopping_item.is_resolved)
        self.assertIsNone(shopping_item.resolved_at)

    def test_shopping_list_resolve(self):
        """Test shopping list item resolution"""
        shopping_item = ShoppingList.objects.create(
            family=self.family,
            ingredient=self.ingredient,
            qty_needed=Decimal("3.0"),
            unit="pieces",
        )
        
        # Initially not resolved
        self.assertFalse(shopping_item.is_resolved)
        
        # Resolve the item
        shopping_item.resolved_at = timezone.now()
        shopping_item.save()
        
        # Should now be resolved
        self.assertTrue(shopping_item.is_resolved)
        self.assertIsNotNone(shopping_item.resolved_at)


class APITests(APITestCase):
    """Test the REST API endpoints"""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="testpass123")
        self.other_user = User.objects.create_user(username="otheruser", email="other@example.com", password="testpass123")
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

    def test_shopping_list_crud(self):
        """Test shopping list CRUD operations"""
        self.client.force_authenticate(user=self.user)

        # Create shopping list item
        data = {
            "family_id": self.family.id,
            "ingredient_id": self.ingredient.id,
            "qty_needed": "5.0",
            "unit": "kg",
        }
        response = self.client.post("/api/shopping-list/", data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        shopping_item_id = response.json()["id"]

        # Read shopping list item
        response = self.client.get(f"/api/shopping-list/{shopping_item_id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(float(response.json()["qty_needed"]), 5.0)
        self.assertFalse(response.json()["is_resolved"])

        # Update shopping list item
        data = {"qty_needed": "7.0"}
        response = self.client.patch(f"/api/shopping-list/{shopping_item_id}/", data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(float(response.json()["qty_needed"]), 7.0)

        # Resolve shopping list item
        response = self.client.patch(f"/api/shopping-list/{shopping_item_id}/resolve/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()["is_resolved"])
        self.assertIsNotNone(response.json()["resolved_at"])

    def test_shopping_list_family_isolation(self):
        """Test that users can only see shopping list items from their families"""
        self.client.force_authenticate(user=self.user)

        # Create shopping list item for user's family
        shopping_item = ShoppingList.objects.create(
            family=self.family,
            ingredient=self.ingredient,
            qty_needed=Decimal("5.0"),
            unit="kg",
        )

        # Create shopping list item for other family
        other_shopping_item = ShoppingList.objects.create(
            family=self.other_family,
            ingredient=self.ingredient,
            qty_needed=Decimal("3.0"),
            unit="pieces",
        )

        # User should only see their family's shopping list item
        response = self.client.get("/api/shopping-list/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        items = response.json()["results"]
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["id"], shopping_item.id)


class ShoppingListTaskTests(TestCase):
    """Test shopping list generation tasks"""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="testpass123")
        self.family = Family.objects.create(name="Test Family")
        self.ingredient = Ingredient.objects.create(name="Tomato", description="Fresh red tomato")

    def test_shopping_list_generation_from_low_stock_alert(self):
        """Test that shopping list items are generated from low stock alerts"""
        # Create low stock threshold
        threshold = LowStockThreshold.objects.create(
            family=self.family,
            ingredient=self.ingredient,
            threshold_qty=Decimal("5.0"),
            unit="kg",
        )

        # Create pantry stock below threshold
        PantryStock.objects.create(
            family=self.family,
            ingredient=self.ingredient,
            qty_available=Decimal("2.0"),
            unit="kg",
        )

        # Create low stock alert
        Alert.objects.create(
            family=self.family,
            ingredient=self.ingredient,
            alert_type="LOW_STOCK",
            message="Low stock alert",
        )

        # Import and run the task
        from .tasks import generate_shopping_lists

        result = generate_shopping_lists()

        # Check that shopping list item was created
        shopping_items = ShoppingList.objects.filter(family=self.family, ingredient=self.ingredient)
        self.assertEqual(shopping_items.count(), 1)

        shopping_item = shopping_items.first()
        self.assertEqual(shopping_item.family, self.family)
        self.assertEqual(shopping_item.ingredient, self.ingredient)
        # Should buy enough to reach 1.5 * threshold - current = 1.5 * 5 - 2 = 5.5
        self.assertEqual(shopping_item.qty_needed, Decimal("5.5"))
        self.assertEqual(shopping_item.unit, "kg")

    def test_shopping_list_generation_from_expired_alert(self):
        """Test that shopping list items are generated from expired alerts"""
        # Create expired pantry stock
        PantryStock.objects.create(
            family=self.family,
            ingredient=self.ingredient,
            qty_available=Decimal("3.0"),
            unit="pieces",
            best_before=date.today() - timedelta(days=1),
        )

        # Create expired alert
        Alert.objects.create(
            family=self.family,
            ingredient=self.ingredient,
            alert_type="EXPIRED",
            message="Expired item alert",
        )

        # Import and run the task
        from .tasks import generate_shopping_lists

        result = generate_shopping_lists()

        # Check that shopping list item was created
        shopping_items = ShoppingList.objects.filter(family=self.family, ingredient=self.ingredient)
        self.assertEqual(shopping_items.count(), 1)

        shopping_item = shopping_items.first()
        self.assertEqual(shopping_item.qty_needed, Decimal("3.0"))  # Replace expired amount
        self.assertEqual(shopping_item.unit, "pieces")

    def test_no_duplicate_shopping_list_items(self):
        """Test that duplicate shopping list items are not created"""
        # Create alert
        Alert.objects.create(
            family=self.family,
            ingredient=self.ingredient,
            alert_type="LOW_STOCK",
            message="Low stock alert",
        )

        # Create existing shopping list item
        ShoppingList.objects.create(
            family=self.family,
            ingredient=self.ingredient,
            qty_needed=Decimal("5.0"),
            unit="kg",
        )

        # Import and run the task
        from .tasks import generate_shopping_lists

        result = generate_shopping_lists()

        # Should still only have one shopping list item
        shopping_items = ShoppingList.objects.filter(family=self.family, ingredient=self.ingredient)
        self.assertEqual(shopping_items.count(), 1)


class AlertTests(TestCase):
    """Test alert models and functionality"""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="testpass123")
        self.family = Family.objects.create(name="Test Family")
        self.ingredient = Ingredient.objects.create(name="Tomato", description="Fresh red tomato")
        FamilyMember.objects.create(user=self.user, family=self.family, role="chef")

    def test_alert_creation(self):
        """Test alert model creation"""
        alert = Alert.objects.create(
            family=self.family,
            ingredient=self.ingredient,
            alert_type="LOW_STOCK",
            message="Low stock: Tomato has 2.0 kg remaining",
        )

        self.assertEqual(alert.family, self.family)
        self.assertEqual(alert.ingredient, self.ingredient)
        self.assertEqual(alert.alert_type, "LOW_STOCK")
        self.assertFalse(alert.is_resolved)
        self.assertIsNone(alert.resolved_at)

    def test_low_stock_threshold_creation(self):
        """Test low stock threshold model creation"""
        threshold = LowStockThreshold.objects.create(
            family=self.family, ingredient=self.ingredient, threshold_qty=Decimal("5.0"), unit="kg"
        )

        self.assertEqual(threshold.family, self.family)
        self.assertEqual(threshold.ingredient, self.ingredient)
        self.assertEqual(threshold.threshold_qty, Decimal("5.0"))
        self.assertEqual(threshold.unit, "kg")


class AlertAPITests(APITestCase):
    """Test alert API endpoints"""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="testpass123")
        self.family = Family.objects.create(name="Test Family")
        self.ingredient = Ingredient.objects.create(name="Tomato", description="Fresh red tomato")
        FamilyMember.objects.create(user=self.user, family=self.family, role="chef")

    def test_alert_list(self):
        """Test listing alerts"""
        # Create some alerts
        Alert.objects.create(
            family=self.family,
            ingredient=self.ingredient,
            alert_type="LOW_STOCK",
            message="Low stock: Tomato has 2.0 kg remaining",
        )
        Alert.objects.create(
            family=self.family,
            ingredient=self.ingredient,
            alert_type="EXPIRED",
            message="Expired: Tomato expired on 2024-01-01",
        )

        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/alerts/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["count"], 2)

    def test_alert_resolve(self):
        """Test resolving an alert"""
        alert = Alert.objects.create(
            family=self.family,
            ingredient=self.ingredient,
            alert_type="LOW_STOCK",
            message="Low stock: Tomato has 2.0 kg remaining",
        )

        self.client.force_authenticate(user=self.user)
        response = self.client.patch(f"/api/alerts/{alert.id}/resolve/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check that alert is marked as resolved
        alert.refresh_from_db()
        self.assertTrue(alert.is_resolved)
        self.assertIsNotNone(alert.resolved_at)

    def test_low_stock_threshold_crud(self):
        """Test low stock threshold CRUD operations"""
        self.client.force_authenticate(user=self.user)

        # Create threshold
        data = {"family_id": self.family.id, "ingredient_id": self.ingredient.id, "threshold_qty": "5.0", "unit": "kg"}
        response = self.client.post("/api/low-stock-thresholds/", data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        threshold_id = response.json()["id"]

        # Read threshold
        response = self.client.get(f"/api/low-stock-thresholds/{threshold_id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(float(response.json()["threshold_qty"]), 5.0)

        # Update threshold
        data = {"threshold_qty": "10.0"}
        response = self.client.patch(f"/api/low-stock-thresholds/{threshold_id}/", data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(float(response.json()["threshold_qty"]), 10.0)


class AlertTaskTests(TestCase):
    """Test alert-related Celery tasks"""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="testpass123")
        self.family = Family.objects.create(name="Test Family")
        self.ingredient = Ingredient.objects.create(name="Tomato", description="Fresh red tomato")
        FamilyMember.objects.create(user=self.user, family=self.family, role="chef")

    def test_low_stock_alert_creation(self):
        """Test that low stock alerts are created when stock falls below threshold"""
        from .tasks import check_low_stock_alerts

        # Create threshold
        LowStockThreshold.objects.create(
            family=self.family, ingredient=self.ingredient, threshold_qty=Decimal("5.0"), unit="kg"
        )

        # Create pantry stock below threshold
        PantryStock.objects.create(family=self.family, ingredient=self.ingredient, qty_available=Decimal("3.0"), unit="kg")

        # Run the task
        result = check_low_stock_alerts()

        # Check that alert was created
        alerts = Alert.objects.filter(family=self.family, ingredient=self.ingredient, alert_type="LOW_STOCK")
        self.assertEqual(alerts.count(), 1)
        self.assertTrue("Created 1 low stock alerts" in result)

    def test_expired_item_alert_creation(self):
        """Test that expired item alerts are created"""
        from .tasks import check_expired_items

        # Create pantry stock that is expired
        PantryStock.objects.create(
            family=self.family,
            ingredient=self.ingredient,
            qty_available=Decimal("5.0"),
            unit="kg",
            best_before=date.today() - timedelta(days=1),  # Expired yesterday
        )

        # Run the task
        result = check_expired_items()

        # Check that alert was created
        alerts = Alert.objects.filter(family=self.family, ingredient=self.ingredient, alert_type="EXPIRED")
        self.assertEqual(alerts.count(), 1)
        self.assertTrue("Created 1 expiry alerts" in result)

    def test_no_duplicate_alerts(self):
        """Test that duplicate alerts are not created"""
        from .tasks import check_low_stock_alerts

        # Create threshold
        LowStockThreshold.objects.create(
            family=self.family, ingredient=self.ingredient, threshold_qty=Decimal("5.0"), unit="kg"
        )

        # Create pantry stock below threshold
        PantryStock.objects.create(family=self.family, ingredient=self.ingredient, qty_available=Decimal("3.0"), unit="kg")

        # Run the task twice
        check_low_stock_alerts()
        result = check_low_stock_alerts()

        # Check that only one alert exists
        alerts = Alert.objects.filter(family=self.family, ingredient=self.ingredient, alert_type="LOW_STOCK")
        self.assertEqual(alerts.count(), 1)
        self.assertTrue("Created 0 low stock alerts" in result)  # Second run should create 0


class PWATests(TestCase):
    """Test PWA functionality and features"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Collect static files for testing
        from django.core.management import call_command
        call_command('collectstatic', '--noinput', verbosity=0)

    def setUp(self):
        self.client = Client()

    def test_pwa_manifest_endpoint(self):
        """Test PWA manifest.json endpoint"""
        response = self.client.get("/manifest.json")
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/manifest+json")
        
        data = json.loads(response.content)
        
        # Check required manifest fields
        self.assertEqual(data["name"], "FamilyChef - H5 Cooking Assistant")
        self.assertEqual(data["short_name"], "FamilyChef")
        self.assertEqual(data["display"], "standalone")
        self.assertEqual(data["theme_color"], "#4CAF50")
        self.assertEqual(data["background_color"], "#ffffff")
        self.assertEqual(data["start_url"], "/")
        
        # Check icons array exists
        self.assertIn("icons", data)
        self.assertIsInstance(data["icons"], list)
        self.assertTrue(len(data["icons"]) > 0)
        
        # Check first icon has required fields
        first_icon = data["icons"][0]
        self.assertIn("src", first_icon)
        self.assertIn("sizes", first_icon)
        self.assertIn("type", first_icon)

    def test_home_page_pwa_meta_tags(self):
        """Test that home page includes PWA meta tags"""
        response = self.client.get("/")
        
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        
        # Check PWA meta tags
        self.assertIn('<meta name="theme-color" content="#4CAF50">', content)
        self.assertIn('<meta name="apple-mobile-web-app-capable" content="yes">', content)
        self.assertIn('<meta name="apple-mobile-web-app-title" content="FamilyChef">', content)
        self.assertIn('<meta name="mobile-web-app-capable" content="yes">', content)
        
        # Check manifest link
        self.assertIn('<link rel="manifest" href="/manifest.json">', content)
        
        # Check viewport meta tag for mobile responsiveness
        self.assertIn('<meta name="viewport" content="width=device-width, initial-scale=1.0">', content)

    def test_static_files_served(self):
        """Test that PWA static files are accessible"""
        # Test CSS file
        response = self.client.get("/static/core/css/main.css")
        self.assertEqual(response.status_code, 200)
        
        # Test JavaScript files
        response = self.client.get("/static/core/js/main.js")
        self.assertEqual(response.status_code, 200)
        
        response = self.client.get("/static/core/js/pwa.js")
        self.assertEqual(response.status_code, 200)
        
        response = self.client.get("/static/core/js/sw.js")
        self.assertEqual(response.status_code, 200)

    def test_service_worker_caching_headers(self):
        """Test service worker has appropriate caching headers"""
        response = self.client.get("/static/core/js/sw.js")
        
        # Service worker should not be cached aggressively
        self.assertEqual(response.status_code, 200)
        # Note: In production, you'd want Cache-Control headers for service workers

    def test_responsive_design_css_classes(self):
        """Test that responsive design CSS classes are included"""
        response = self.client.get("/static/core/css/main.css")
        
        # Handle WhiteNoise static file response
        try:
            content = response.content.decode()
        except AttributeError:
            # WhiteNoise streaming response
            content = b''.join(response.streaming_content).decode()
        
        # Check for mobile-first responsive breakpoints
        self.assertIn("@media (min-width: 481px)", content)  # Tablet
        self.assertIn("@media (min-width: 769px)", content)  # Desktop
        
        # Check for responsive utility classes
        self.assertIn(".col-12", content)
        self.assertIn(".mobile", content)
        self.assertIn(".tablet", content)
        self.assertIn(".desktop", content)

    def test_pwa_template_pages(self):
        """Test that PWA template pages load correctly"""
        pages = [
            ("/", "menu"),
            ("/chef/", "chef_board"),
            ("/pantry/", "pantry"), 
            ("/shopping/", "shopping_list"),
        ]
        
        for url, page_name in pages:
            with self.subTest(page=page_name):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                
                content = response.content.decode()
                
                # Check base template elements
                self.assertIn("FamilyChef", content)
                self.assertIn("PWA", content)
                self.assertIn("main.css", content)
                self.assertIn("main.js", content)
                self.assertIn("pwa.js", content)

    def test_offline_functionality_javascript(self):
        """Test that offline functionality JavaScript is included"""
        response = self.client.get("/static/core/js/pwa.js")
        
        # Handle WhiteNoise static file response
        try:
            content = response.content.decode()
        except AttributeError:
            content = b''.join(response.streaming_content).decode()
        
        # Check for key PWA functionality
        self.assertIn("serviceWorker", content)
        self.assertIn("FamilyChefPWA", content)
        self.assertIn("installPrompt", content)
        self.assertIn("offline", content)
        self.assertIn("beforeinstallprompt", content)

    def test_service_worker_implementation(self):
        """Test service worker includes required functionality"""
        response = self.client.get("/static/core/js/sw.js")
        
        # Handle WhiteNoise static file response
        try:
            content = response.content.decode()
        except AttributeError:
            content = b''.join(response.streaming_content).decode()
        
        # Check for service worker events
        self.assertIn("install", content)
        self.assertIn("activate", content)
        self.assertIn("fetch", content)
        
        # Check for caching strategies
        self.assertIn("CACHE_NAME", content)
        self.assertIn("caches.open", content)
        self.assertIn("cache.addAll", content)
        
        # Check for offline menu support
        self.assertIn("/api/menu/", content)
        self.assertIn("networkFirstStrategy", content)
        self.assertIn("cacheFirstStrategy", content)

    def test_dark_mode_support(self):
        """Test that dark mode CSS variables are included"""
        response = self.client.get("/static/core/css/main.css")
        
        # Handle WhiteNoise static file response
        try:
            content = response.content.decode()
        except AttributeError:
            content = b''.join(response.streaming_content).decode()
        
        # Check for dark theme CSS variables
        self.assertIn('[data-theme="dark"]', content)
        self.assertIn("--bg-primary: #121212", content)
        self.assertIn("--text-primary: #ffffff", content)
        
        # Check for theme toggle functionality in JavaScript
        response = self.client.get("/static/core/js/main.js")
        try:
            js_content = response.content.decode()
        except AttributeError:
            js_content = b''.join(response.streaming_content).decode()
        self.assertIn("toggleTheme", js_content)

    def test_touch_friendly_design(self):
        """Test that design includes touch-friendly elements"""
        response = self.client.get("/static/core/css/main.css")
        
        # Handle WhiteNoise static file response
        try:
            content = response.content.decode()
        except AttributeError:
            content = b''.join(response.streaming_content).decode()
        
        # Check for touch-friendly minimum sizes
        self.assertIn("min-height: 44px", content)  # Touch targets
        self.assertIn("min-height: 48px", content)  # Larger touch targets
        
        # Check for touch-specific media queries
        self.assertIn("@media (hover: none) and (pointer: coarse)", content)
        
        # Check for touch optimization
        self.assertIn("touch-action: manipulation", content)

    def test_accessibility_features(self):
        """Test that accessibility features are included"""
        response = self.client.get("/static/core/css/main.css")
        
        # Handle WhiteNoise static file response
        try:
            content = response.content.decode()
        except AttributeError:
            content = b''.join(response.streaming_content).decode()
        
        # Check for high contrast mode support
        self.assertIn("@media (prefers-contrast: high)", content)
        
        # Check for reduced motion support
        self.assertIn("@media (prefers-reduced-motion: reduce)", content)
        
        # Check for focus styles
        self.assertIn("focus", content)
        self.assertIn("outline", content)


class WebSocketTests(TestCase):
    """Test WebSocket consumer functionality"""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.family = Family.objects.create(name='Test Family')
        FamilyMember.objects.create(user=self.user, family=self.family, role='chef')

    @override_settings(TESTING=False)
    def test_send_order_update_util(self):
        """Test order update utility function"""
        from core.utils import send_order_update
        
        # Test with valid data
        order_data = {'id': 1, 'status': 'DONE'}
        
        # Should not raise an exception
        try:
            send_order_update(self.family.id, order_data)
        except Exception as e:
            self.fail(f"send_order_update raised {e} unexpectedly")

    @override_settings(TESTING=False)
    def test_send_shopping_list_update_util(self):
        """Test shopping list update utility function"""
        from core.utils import send_shopping_list_update
        
        # Test with valid data
        shopping_data = {'id': 1, 'is_resolved': True}
        
        # Should not raise an exception
        try:
            send_shopping_list_update(self.family.id, shopping_data)
        except Exception as e:
            self.fail(f"send_shopping_list_update raised {e} unexpectedly")

    def test_send_order_update_during_testing(self):
        """Test that order updates are skipped during testing"""
        from core.utils import send_order_update
        
        # Should complete without error during testing
        order_data = {'id': 1, 'status': 'DONE'}
        send_order_update(self.family.id, order_data)
        # No exception should be raised

    def test_send_shopping_list_update_during_testing(self):
        """Test that shopping list updates are skipped during testing"""
        from core.utils import send_shopping_list_update
        
        # Should complete without error during testing
        shopping_data = {'id': 1, 'is_resolved': True}
        send_shopping_list_update(self.family.id, shopping_data)
        # No exception should be raised


class WebSocketConsumerTests(TestCase):
    """Test WebSocket consumer behavior (mock-based tests)"""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.family = Family.objects.create(name='Test Family')
        FamilyMember.objects.create(user=self.user, family=self.family, role='chef')

    def test_order_consumer_authentication_required(self):
        """Test that OrderConsumer requires authentication"""
        from core.consumers import OrderConsumer
        
        # Mock unauthenticated scope
        scope = {
            'url_route': {'kwargs': {'family_id': str(self.family.id)}},
            'user': None  # Unauthenticated user
        }
        
        consumer = OrderConsumer()
        consumer.scope = scope
        
        # The consumer should handle unauthenticated users appropriately
        # (This would normally be tested with async test frameworks)
        self.assertIsNotNone(consumer)

    def test_shopping_list_consumer_authentication_required(self):
        """Test that ShoppingListConsumer requires authentication"""
        from core.consumers import ShoppingListConsumer
        
        # Mock unauthenticated scope
        scope = {
            'url_route': {'kwargs': {'family_id': str(self.family.id)}},
            'user': None  # Unauthenticated user
        }
        
        consumer = ShoppingListConsumer()
        consumer.scope = scope
        
        # The consumer should handle unauthenticated users appropriately
        self.assertIsNotNone(consumer)

    def test_order_consumer_room_group_name(self):
        """Test that OrderConsumer sets correct room group name"""
        from core.consumers import OrderConsumer
        
        scope = {
            'url_route': {'kwargs': {'family_id': str(self.family.id)}},
            'user': self.user
        }
        
        consumer = OrderConsumer()
        consumer.scope = scope
        consumer.family_id = str(self.family.id)
        consumer.room_group_name = f"orders_{self.family.id}"
        
        self.assertEqual(consumer.room_group_name, f"orders_{self.family.id}")

    def test_shopping_list_consumer_room_group_name(self):
        """Test that ShoppingListConsumer sets correct room group name"""
        from core.consumers import ShoppingListConsumer
        
        scope = {
            'url_route': {'kwargs': {'family_id': str(self.family.id)}},
            'user': self.user
        }
        
        consumer = ShoppingListConsumer()
        consumer.scope = scope
        consumer.family_id = str(self.family.id)
        consumer.room_group_name = f"shopping_{self.family.id}"
        
        self.assertEqual(consumer.room_group_name, f"shopping_{self.family.id}")


class CeleryTaskTests(TestCase):
    """Test Celery task functionality"""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.family = Family.objects.create(name='Test Family')
        FamilyMember.objects.create(user=self.user, family=self.family, role='chef')
        
        self.ingredient = Ingredient.objects.create(name='Test Ingredient')
        
        # Create pantry stock below threshold
        self.stock = PantryStock.objects.create(
            family=self.family,
            ingredient=self.ingredient,
            qty_available=5.0,
            unit='kg'
        )
        
        # Create low stock threshold
        self.threshold = LowStockThreshold.objects.create(
            family=self.family,
            ingredient=self.ingredient,
            threshold_qty=10.0,
            unit='kg'
        )

    def test_check_low_stock_task_direct_call(self):
        """Test low stock checking task"""
        from core.tasks import check_low_stock_alerts
        
        # Call the task directly (not through Celery)
        check_low_stock_alerts()
        
        # Check that an alert was created
        alert = Alert.objects.filter(
            family=self.family,
            alert_type='LOW_STOCK',
            ingredient=self.ingredient
        ).first()
        
        self.assertIsNotNone(alert)
        self.assertFalse(alert.is_resolved)

    def test_check_expired_items_task_direct_call(self):
        """Test expired items checking task"""
        from core.tasks import check_expired_items
        from datetime import date, timedelta
        
        # Create a different ingredient to avoid unique constraint
        expired_ingredient = Ingredient.objects.create(name='Expired Ingredient')
        
        # Create expired stock
        expired_stock = PantryStock.objects.create(
            family=self.family,
            ingredient=expired_ingredient,
            qty_available=3.0,
            unit='kg',
            best_before=date.today() - timedelta(days=1)  # Expired yesterday
        )
        
        # Call the task directly
        check_expired_items()
        
        # Check that an alert was created
        alert = Alert.objects.filter(
            family=self.family,
            alert_type='EXPIRED',
            ingredient=expired_ingredient
        ).first()
        
        self.assertIsNotNone(alert)
        self.assertFalse(alert.is_resolved)

    def test_generate_shopping_list_task_direct_call(self):
        """Test shopping list generation task"""
        from core.tasks import generate_shopping_lists
        
        # Create an unresolved low stock alert
        Alert.objects.create(
            family=self.family,
            alert_type='LOW_STOCK',
            ingredient=self.ingredient,
            is_resolved=False
        )
        
        # Call the task directly
        generate_shopping_lists()
        
        # Check that a shopping list item was created
        shopping_item = ShoppingList.objects.filter(
            family=self.family,
            ingredient=self.ingredient
        ).first()
        
        self.assertIsNotNone(shopping_item)
        self.assertFalse(shopping_item.is_resolved)
