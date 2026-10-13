from django.urls import path

from . import views

app_name = "catalog"
urlpatterns = [
    path("", views.resource_list, name="list"),
    path("resources/<str:resource_key>/", views.resource_detail, name="detail"),
    path("api/public/resources", views.api_public_resources, name="api_list"),
]
