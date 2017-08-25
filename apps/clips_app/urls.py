from django.conf.urls import url
from .views import ClipContainer

urlpatterns = [
    url(r'^container$', ClipContainer.as_view(), name='clip-container'),
]