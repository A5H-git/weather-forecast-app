from django.urls import path

from weather.views import Index

urlpatterns = [
    path("", Index.as_view(), name="index"),
]
