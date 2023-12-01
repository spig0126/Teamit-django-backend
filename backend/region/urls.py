from django.urls import path

from . import views

urlpatterns = [
     path('city/<int:pk>/', views.CityDetailAPIView.as_view()), 
     path('city/<str:name>/', views.CityDetailAPIView.as_view()), 
     path('province/<int:pk>/', views.ProvinceDetailAPIView.as_view()), 
     path('province/<str:name>/', views.ProvinceDetailAPIView.as_view()), 
     path('', views.CityListAPIView.as_view()),
]
