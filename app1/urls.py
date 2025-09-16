from django.urls import path
from . import views

app_name = "invoices"

urlpatterns = [
    path("", views.invoice_list, name="list"),
    path("create/", views.invoice_create, name="create"),
    path("<int:pk>/preview/", views.invoice_preview, name="preview"),
    path("<int:pk>/generate-pdf/", views.invoice_generate_pdf, name="generate_pdf"),
    path("<int:pk>/download/", views.invoice_download, name="download"),
    path("<int:pk>/delete/", views.invoice_delete, name="delete"),
    path("register/", views.register, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
]
