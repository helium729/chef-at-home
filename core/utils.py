from django.conf import settings
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


def send_order_update(family_id, order_data):
    """Send order update to WebSocket group"""
    # Skip WebSocket notifications during testing
    if settings.TESTING:
        return
        
    channel_layer = get_channel_layer()
    if channel_layer:
        try:
            async_to_sync(channel_layer.group_send)(
                f'orders_{family_id}',
                {
                    'type': 'order_update',
                    'message': {
                        'action': 'order_updated',
                        'order': order_data
                    }
                }
            )
        except Exception:
            # Silently fail if Redis is not available (e.g., during testing)
            pass