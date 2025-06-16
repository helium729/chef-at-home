"""
Celery tasks for background processing
"""

from datetime import date, timedelta
from decimal import Decimal

from celery import shared_task

from .models import Alert, Family, LowStockThreshold, PantryStock, ShoppingList


@shared_task
def check_low_stock_alerts():
    """
    Check for low stock conditions and create alerts
    """
    alerts_created = 0

    # Get all families
    families = Family.objects.all()

    for family in families:
        # Get pantry stock for this family
        pantry_items = PantryStock.objects.filter(family=family)

        for pantry_item in pantry_items:
            # Check if there's a threshold configured for this ingredient
            try:
                threshold = LowStockThreshold.objects.get(family=family, ingredient=pantry_item.ingredient)

                # Simple unit comparison - assumes same units for now
                # TODO: Add unit conversion logic
                if pantry_item.unit == threshold.unit and pantry_item.qty_available <= threshold.threshold_qty:

                    # Check if there's already an active alert for this
                    existing_alert = Alert.objects.filter(
                        family=family, ingredient=pantry_item.ingredient, alert_type="LOW_STOCK", is_resolved=False
                    ).exists()

                    if not existing_alert:
                        Alert.objects.create(
                            family=family,
                            ingredient=pantry_item.ingredient,
                            alert_type="LOW_STOCK",
                            message=f"Low stock: {pantry_item.ingredient.name} has "
                            f"{pantry_item.qty_available} {pantry_item.unit} remaining "
                            f"(threshold: {threshold.threshold_qty} {threshold.unit})",
                        )
                        alerts_created += 1

            except LowStockThreshold.DoesNotExist:
                # No threshold configured for this ingredient, skip
                continue

    return f"Created {alerts_created} low stock alerts"


@shared_task
def check_expired_items():
    """
    Check for expired items and create alerts
    """
    alerts_created = 0
    today = date.today()

    # Find all pantry items that are expired or expiring soon (within 3 days)
    expiring_items = PantryStock.objects.filter(best_before__isnull=False, best_before__lte=today + timedelta(days=3))

    for item in expiring_items:
        # Determine alert type based on expiry date
        if item.best_before <= today:
            alert_type = "EXPIRED"
            message = f"Expired: {item.ingredient.name} expired on {item.best_before}"
        else:
            # For items expiring soon, we'll still use EXPIRED type but with different message
            days_until_expiry = (item.best_before - today).days
            alert_type = "EXPIRED"
            message = f"Expiring soon: {item.ingredient.name} expires in {days_until_expiry} day(s) on {item.best_before}"

        # Check if there's already an active alert for this item
        existing_alert = Alert.objects.filter(
            family=item.family, ingredient=item.ingredient, alert_type="EXPIRED", is_resolved=False
        ).exists()

        if not existing_alert:
            Alert.objects.create(family=item.family, ingredient=item.ingredient, alert_type=alert_type, message=message)
            alerts_created += 1

    return f"Created {alerts_created} expiry alerts"


@shared_task
def daily_alert_check():
    """
    Combined daily task to check both low stock and expired items
    """
    low_stock_result = check_low_stock_alerts()
    expiry_result = check_expired_items()

    return f"Daily alert check completed. {low_stock_result}. {expiry_result}."


@shared_task
def generate_shopping_lists():
    """
    Generate shopping lists from active alerts
    """
    items_created = 0

    # Get all families
    families = Family.objects.all()

    for family in families:
        # Get all active low stock and expired alerts for this family
        active_alerts = Alert.objects.filter(family=family, is_resolved=False)

        for alert in active_alerts:
            # Check if there's already a shopping list item for this ingredient
            existing_item = ShoppingList.objects.filter(
                family=family, ingredient=alert.ingredient, resolved_at__isnull=True
            ).first()

            if existing_item:
                # Update quantity if there's a specific need (for now, skip)
                continue

            # Determine quantity needed based on alert type
            if alert.alert_type == "LOW_STOCK":
                # Try to get the threshold to know how much to buy
                try:
                    threshold = LowStockThreshold.objects.get(family=family, ingredient=alert.ingredient)
                    # Buy enough to reach threshold + 50% buffer
                    current_stock = PantryStock.objects.get(family=family, ingredient=alert.ingredient)
                    qty_needed = (threshold.threshold_qty * Decimal("1.5")) - current_stock.qty_available
                    unit = threshold.unit
                except (LowStockThreshold.DoesNotExist, PantryStock.DoesNotExist):
                    # Default to buying 1 unit if we can't determine specifics
                    qty_needed = Decimal("1.0")
                    unit = "unit"
            else:  # EXPIRED
                # For expired items, buy a standard replacement amount
                try:
                    expired_stock = PantryStock.objects.get(family=family, ingredient=alert.ingredient)
                    qty_needed = expired_stock.qty_available  # Replace the expired amount
                    unit = expired_stock.unit
                except PantryStock.DoesNotExist:
                    qty_needed = Decimal("1.0")
                    unit = "unit"

            # Ensure positive quantity
            if qty_needed > 0:
                ShoppingList.objects.create(
                    family=family, ingredient=alert.ingredient, qty_needed=qty_needed, unit=unit
                )
                items_created += 1

    return f"Generated {items_created} shopping list items"


@shared_task
def daily_shopping_list_generation():
    """
    Combined daily task to generate shopping lists after alert checks
    """
    alert_result = daily_alert_check()
    shopping_result = generate_shopping_lists()

    return f"Daily tasks completed. {alert_result} {shopping_result}"
