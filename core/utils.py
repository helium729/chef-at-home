from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings


def send_order_update(family_id, order_data):
    """Send order update to WebSocket group"""
    # Skip WebSocket notifications during testing
    if settings.TESTING:
        return

    channel_layer = get_channel_layer()
    if channel_layer:
        try:
            async_to_sync(channel_layer.group_send)(
                f"orders_{family_id}", {"type": "order_update", "message": {"action": "order_updated", "order": order_data}}
            )
        except Exception:
            # Silently fail if Redis is not available (e.g., during testing)
            pass


def send_shopping_list_update(family_id, shopping_item_data):
    """Send shopping list update to WebSocket group"""
    # Skip WebSocket notifications during testing
    if settings.TESTING:
        return

    channel_layer = get_channel_layer()
    if channel_layer:
        try:
            async_to_sync(channel_layer.group_send)(
                f"shopping_{family_id}",
                {"type": "shopping_list_update", "message": {"action": "shopping_list_updated", "item": shopping_item_data}},
            )
        except Exception:
            # Silently fail if Redis is not available (e.g., during testing)
            pass
