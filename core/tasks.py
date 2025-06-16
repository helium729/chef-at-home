"""
Celery tasks for background processing
"""

from datetime import date, timedelta

from celery import shared_task

from .models import Alert, Family, LowStockThreshold, PantryStock


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
