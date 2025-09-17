from django.db import models, transaction
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models

from django.utils import timezone
from decimal import Decimal, ROUND_HALF_UP

User = settings.AUTH_USER_MODEL  # Custom user support (username, password, mobile)

# ----------------------
# Company (Seller)
# ----------------------
class Company(models.Model):
    """Main seller details — 1 row for your wholesale business."""
    name = models.CharField(max_length=200)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    pincode = models.CharField(max_length=20)
    state = models.CharField(max_length=100)
    state_code = models.CharField(max_length=5)
    gstin = models.CharField(max_length=20, blank=True)
    bank_account = models.CharField(max_length=200, blank=True)
    ifsc = models.CharField(max_length=50, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)

    def __str__(self):
        return self.name


# ----------------------
# Parties (From & To)
# ----------------------
class Party(models.Model):
    """Both From & To parties stored here."""
    name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=200)
    phone = models.CharField(max_length=30)
    email = models.EmailField()
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    pincode = models.CharField(max_length=20)
    state = models.CharField(max_length=100)
    tax_state_code = models.CharField(max_length=5)
    gstin = models.CharField(max_length=20, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.name


# ----------------------
# Units
# ----------------------
class Unit(models.Model):
    label = models.CharField(max_length=20)  # e.g. DOZ, BOX
    how_many_pieces = models.PositiveIntegerField()  # 1 DOZ = 12 PCS
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.label} = {self.how_many_pieces} pcs"


# ----------------------
# Taxes
# ----------------------
class Tax(models.Model):
    name = models.CharField(max_length=50)   # GST 18%
    rate_percent = models.DecimalField(max_digits=5, decimal_places=2)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({self.rate_percent}%)"


# ----------------------
# Products
# ----------------------

class CustomUser(AbstractUser):
    """Custom user with mobile field."""
    mobile = models.CharField(max_length=15, unique=True)

    def __str__(self):
        return self.username


# ----------------------
# Invoice Sequence
# ----------------------
class InvoiceSequence(models.Model):
    """One row to store last invoice number."""
    last_number = models.PositiveIntegerField(default=0)


from decimal import Decimal, ROUND_HALF_UP
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# ----------------------
# Product
# ----------------------
class Product(models.Model):
    sku = models.CharField(max_length=50, blank=True)
    name = models.CharField(max_length=255)
    pic = models.ImageField(upload_to='products/', blank=True, null=True)
    rate = models.DecimalField(max_digits=12, decimal_places=2)  # tax-exclusive
    hsn_sac = models.CharField(max_length=20, default='3306', blank=True)
    default_tax = models.ForeignKey("Tax", on_delete=models.SET_NULL, null=True, blank=True)
    default_unit = models.ForeignKey("Unit", on_delete=models.SET_NULL, null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)


    def __str__(self):
        return self.name


# ----------------------
# Invoice
# ----------------------
class Invoice(models.Model):
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    invoice_number = models.CharField(max_length=50, unique=True)  # e.g. INV_0001_20250915
    seq_number = models.PositiveIntegerField()
    date = models.DateField(default=timezone.localdate)  # editable
    from_party = models.ForeignKey("Party", related_name="from_invoices", on_delete=models.PROTECT)
    to_party = models.ForeignKey("Party", related_name="to_invoices", on_delete=models.PROTECT)
    overall_discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    apply_gst = models.BooleanField(default=False)
    tax = models.ForeignKey("Tax", on_delete=models.SET_NULL, null=True, blank=True)
    is_igst = models.BooleanField(default=False)
    pdf_file = models.FileField(upload_to="invoices/", null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    version = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-seq_number"]

    def __str__(self):
        return self.invoice_number

    # Totals
    def taxable_subtotal(self):
        return sum((item.line_taxable_amount() for item in self.items.all()), Decimal("0.00"))

    def total_discount_amount(self):
        subtotal = self.taxable_subtotal()
        if self.overall_discount_percent:
            return (subtotal * self.overall_discount_percent / 100).quantize(Decimal("0.01"), ROUND_HALF_UP)
        return Decimal("0.00")

    def tax_amounts(self):
        subtotal = self.taxable_subtotal() - self.total_discount_amount()
        if not self.apply_gst or not self.tax:
            return {"cgst": Decimal("0.00"), "sgst": Decimal("0.00"), "igst": Decimal("0.00")}
        rate = self.tax.rate_percent
        if self.is_igst:
            igst = (subtotal * rate / 100).quantize(Decimal("0.01"), ROUND_HALF_UP)
            return {"igst": igst, "cgst": Decimal("0.00"), "sgst": Decimal("0.00")}
        half = rate / 2
        cgst = (subtotal * half / 100).quantize(Decimal("0.01"), ROUND_HALF_UP)
        return {"igst": Decimal("0.00"), "cgst": cgst, "sgst": cgst}

    def grand_total(self):
        subtotal = self.taxable_subtotal() - self.total_discount_amount()
        taxes = self.tax_amounts()
        total = subtotal + taxes["cgst"] + taxes["sgst"] + taxes["igst"]
        return total.quantize(Decimal("0.01"), ROUND_HALF_UP)


# ----------------------
# Invoice Items
# ----------------------
class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT, null=True, blank=True)
    description = models.CharField(max_length=400, blank=True)
    hsn_sac = models.CharField(max_length=20, blank=True)
    unit = models.ForeignKey("Unit", on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=12, decimal_places=3)
    rate = models.DecimalField(max_digits=12, decimal_places=2)  # tax-exclusive
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    def line_amount(self):
        return (self.rate * self.quantity).quantize(Decimal("0.01"), ROUND_HALF_UP)

    def line_discount_amount(self):
        return (self.line_amount() * self.discount_percent / 100).quantize(Decimal("0.01"), ROUND_HALF_UP)

    def line_taxable_amount(self):
        return self.line_amount() - self.line_discount_amount()

    def __str__(self):
        return f"{self.product} ({self.quantity} x {self.rate})"

# ----------------------
# Audit log
# ----------------------
class InvoiceAudit(models.Model):
    invoice = models.ForeignKey(Invoice, related_name='audits', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    action = models.CharField(max_length=50)  # created/updated/deleted/pdf_generated
    timestamp = models.DateTimeField(auto_now_add=True)
    note = models.TextField(blank=True)
    diff = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"{self.invoice.invoice_number} - {self.action} at {self.timestamp}"
