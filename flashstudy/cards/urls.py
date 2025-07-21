from django.urls import path
from . import views


"""  Checkout URLs  """
urlpatterns = [
    path('', views.home, name='home'),
]