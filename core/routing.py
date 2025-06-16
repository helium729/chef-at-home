from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r"ws/orders/(?P<family_id>\w+)/$", consumers.OrderConsumer.as_asgi()),
    re_path(r"ws/shopping/(?P<family_id>\w+)/$", consumers.ShoppingListConsumer.as_asgi()),
]
