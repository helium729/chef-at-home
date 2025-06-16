from django.contrib.auth.models import User
from django.db import models


class Family(models.Model):
    """Family group that users can belong to"""

    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "families"

    def __str__(self):
        return self.name


class FamilyMember(models.Model):
    """Junction table for User-Family M2M relationship"""

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    family = models.ForeignKey(Family, on_delete=models.CASCADE)
    role = models.CharField(
        max_length=20,
        choices=[
            ("member", "Member"),
            ("chef", "Chef"),
            ("admin", "Admin"),
        ],
        default="member",
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["user", "family"]

    def __str__(self):
        return f"{self.user.username} - {self.family.name} ({self.role})"


class Ingredient(models.Model):
    """Base ingredient that can be used in recipes and tracked in pantry"""

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Cuisine(models.Model):
    """Recipe/dish that can be cooked"""

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    default_time_min = models.PositiveIntegerField(help_text="Default cooking time in minutes")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    family = models.ForeignKey(Family, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["name", "family"]

    def __str__(self):
        return f"{self.name} ({self.family.name})"
    
    def is_available(self):
        """Check if this cuisine can be made with current pantry stock"""
        for recipe_ingredient in self.recipe_ingredients.all():
            if recipe_ingredient.is_optional:
                continue
                
            try:
                pantry_stock = PantryStock.objects.get(
                    family=self.family,
                    ingredient=recipe_ingredient.ingredient
                )
                
                # Simple unit comparison - assumes same units for now
                # TODO: Add unit conversion logic
                if pantry_stock.qty_available < recipe_ingredient.quantity:
                    # Check if there's a substitutable ingredient available
                    if not recipe_ingredient.is_substitutable:
                        return False
                    # TODO: Add substitution logic
                    
            except PantryStock.DoesNotExist:
                if not recipe_ingredient.is_substitutable:
                    return False
                # TODO: Add substitution logic
                
        return True


class RecipeIngredient(models.Model):
    """Junction table for Cuisine-Ingredient relationship with quantities"""

    cuisine = models.ForeignKey(Cuisine, on_delete=models.CASCADE, related_name="recipe_ingredients")
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=20)
    is_optional = models.BooleanField(default=False)
    is_substitutable = models.BooleanField(default=False)

    class Meta:
        unique_together = ["cuisine", "ingredient"]

    def __str__(self):
        return f"{self.cuisine.name}: {self.quantity} {self.unit} {self.ingredient.name}"


class PantryStock(models.Model):
    """Tracks available ingredients in family pantry"""

    family = models.ForeignKey(Family, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    qty_available = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=20)
    best_before = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["family", "ingredient"]

    def __str__(self):
        return f"{self.family.name}: {self.qty_available} {self.unit} {self.ingredient.name}"


class Order(models.Model):
    """Order placed by family member for a specific cuisine"""
    
    STATUS_CHOICES = [
        ("NEW", "New"),
        ("COOKING", "Cooking"),
        ("DONE", "Done"),
    ]
    
    family = models.ForeignKey(Family, on_delete=models.CASCADE)
    cuisine = models.ForeignKey(Cuisine, on_delete=models.CASCADE)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="NEW")
    scheduled_for = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Order #{self.id}: {self.cuisine.name} for {self.family.name} ({self.status})"


class OrderItemIngredient(models.Model):
    """Snapshot of ingredients used in an order for historical accuracy"""
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="order_ingredients")
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=20)
    
    def __str__(self):
        return f"Order #{self.order.id}: {self.quantity} {self.unit} {self.ingredient.name}"
