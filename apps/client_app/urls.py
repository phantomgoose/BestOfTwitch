from django.conf.urls import url
from .views import ClientIndex

urlpatterns = [
    url(r'^', ClientIndex.as_view(), name='client-index'),
]