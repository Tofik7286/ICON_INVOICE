from django.urls import include, path
from . import views

app_name = "invoices"

urlpatterns = [
    path("", views.invoice_list, name="list"),
    path("create/", views.invoice_create, name="create"),
    path("<int:pk>/preview/", views.invoice_preview, name="preview"),
    path("<int:pk>/generate-pdf/", views.invoice_generate_pdf, name="generate_pdf"),
    # path("<int:pk>/download/", views.invoice_download, name="download"),
    path("<int:pk>/delete/", views.invoice_delete, name="delete"),
    path("<int:pk>/update/", views.invoice_update, name="update"),
    

]
