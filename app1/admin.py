# app1/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser
from .models import (
    Company, Party, Unit, Tax, Product,
    Invoice, InvoiceItem, InvoiceAudit
)
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ("username", "mobile", "email", "is_staff", "is_active", "last_login")
    search_fields = ("username", "mobile", "email")
    ordering = ("username",)

    fieldsets = (
        (None, {"fields": ("username", "mobile", "email", "password")}),
        ("Permissions", {"fields": ("is_staff", "is_active", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
# ----------------------
# Company
# ----------------------
@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("name", "gstin", "city", "state")
    search_fields = ("name", "gstin", "city")


# ----------------------
# Party
# ----------------------
@admin.register(Party)
class PartyAdmin(admin.ModelAdmin):
    list_display = ("name", "contact_person", "phone", "city", "gstin")
    search_fields = ("name", "phone", "city", "gstin")
    list_filter = ("state",)


# ----------------------
# Unit
# ----------------------
@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ("label", "how_many_pieces")
    search_fields = ("label",)


# ----------------------
# Tax
# ----------------------
@admin.register(Tax)
class TaxAdmin(admin.ModelAdmin):
    list_display = ("name", "rate_percent", "is_default")
    list_filter = ("is_default",)


# ----------------------
# Product
# ----------------------
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "sku", "rate", "hsn_sac", "default_unit")
    search_fields = ("name", "sku", "hsn_sac")
    list_filter = ("default_unit", "default_tax")


# ----------------------
# Inline for Invoice Items
# ----------------------
class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1
    fields = ("product", "description", "hsn_sac", "unit", "quantity", "rate", "discount_percent")
    autocomplete_fields = ("product", "unit")


# ----------------------
# Invoice
# ----------------------
@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = (
        "invoice_number", "date", "from_party", "to_party",
        "grand_total", "apply_gst", "is_deleted"
    )
    search_fields = ("invoice_number", "from_party__name", "to_party__name")
    list_filter = ("apply_gst", "is_deleted", "date")
    readonly_fields = ("invoice_number", "seq_number", "created_at", "updated_at", "version")
    inlines = [InvoiceItemInline]

    def grand_total(self, obj):
        return obj.grand_total()


# ----------------------
# InvoiceAudit
# ----------------------
@admin.register(InvoiceAudit)
class InvoiceAuditAdmin(admin.ModelAdmin):
    list_display = ("invoice", "user", "action", "timestamp")
    list_filter = ("action", "timestamp", "user__is_staff")