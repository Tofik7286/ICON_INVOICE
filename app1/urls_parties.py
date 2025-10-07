from django.urls import path
from . import views

app_name = "parties"

urlpatterns = [
    path("", views.party_list, name="list"),
    path("create/", views.party_create, name="create"),
    path("<int:pk>/update/", views.party_update, name="update"),
    path("<int:pk>/delete/", views.party_delete, name="delete"),
]