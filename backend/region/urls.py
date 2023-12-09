from django.urls import path

from .views import *

urlpatterns = [
     path('cities/<int:pk>/', CityDetailAPIView.as_view()), 
     path('cities/<str:name>/', CityDetailAPIView.as_view()), 
     path('provinces/<int:pk>/', ProvinceDetailAPIView.as_view()), 
     path('provinces/<str:name>/', ProvinceDetailAPIView.as_view()), 
     path('', CityByProvinceListAPIView.as_view()),
]
