from django import forms
from django.forms import inlineformset_factory
from .models import Invoice, InvoiceItem, Party, Product, Unit, Tax
from .models import *

# ----------------------
# Invoice Form
# ----------------------
from django import forms
from django.forms import inlineformset_factory
from .models import Invoice, InvoiceItem


# ----------------------
# Invoice Form
# ----------------------
class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = [
            "date",
            "from_party",
            "to_party",
            "overall_discount_percent",
            "apply_gst",
            "tax",
        ]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "from_party": forms.Select(attrs={"class": "form-select"}),
            "to_party": forms.Select(attrs={"class": "form-select"}),
            "overall_discount_percent": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "apply_gst": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "tax": forms.Select(attrs={"class": "form-select"}),
        }


# ----------------------
# Invoice Item Form
# ----------------------
class InvoiceItemForm(forms.ModelForm):
    class Meta:
        model = InvoiceItem
        fields = [
            "product",
            "description",
            "hsn_sac",
            "unit",
            "quantity",
            "custom_rate",   # 👈 use this
            "discount_percent",
        ]
        widgets = {
            "product": forms.Select(attrs={"class": "form-select"}),
            "description": forms.TextInput(attrs={"class": "form-control", "placeholder": "Item description"}),
            "hsn_sac": forms.TextInput(attrs={"class": "form-control", "readonly": "readonly"}),
            "unit": forms.Select(attrs={"class": "form-select"}),
            "quantity": forms.NumberInput(attrs={"class": "form-control", "step": "0.001"}),
            "custom_rate": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "discount_percent": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pre-fill custom_rate with product rate if not set
        if self.instance and self.instance.rate and not self.instance.custom_rate:
            self.fields["custom_rate"].initial = self.instance.rate

# ----------------------
# Invoice Item Formset
# ----------------------
InvoiceItemFormSet = inlineformset_factory(
    Invoice,
    InvoiceItem,
    form=InvoiceItemForm,
    extra=1,
    can_delete=True
)

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ["username", "mobile", "email", "password1", "password2"]
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "mobile": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
        }


class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"class": "form-control"}))
# ----------------------
# Party Form
# ----------------------
class PartyForm(forms.ModelForm):
    class Meta:
        model = Party
        fields = [
            "name", "contact_person", "phone", "email",
            "address_line1", "address_line2", "city", "pincode",
            "state", "tax_state_code", "gstin"
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "contact_person": forms.TextInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "address_line1": forms.TextInput(attrs={"class": "form-control"}),
            "address_line2": forms.TextInput(attrs={"class": "form-control"}),
            "city": forms.TextInput(attrs={"class": "form-control"}),
            "pincode": forms.TextInput(attrs={"class": "form-control"}),
            "state": forms.TextInput(attrs={"class": "form-control"}),
            "tax_state_code": forms.TextInput(attrs={"class": "form-control"}),
            "gstin": forms.TextInput(attrs={"class": "form-control"}),
        }
# ----------------------
# Product Form
# ----------------------
class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            "name", "sku",  "rate",
            "hsn_sac", "default_tax", "default_unit"
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "sku": forms.TextInput(attrs={"class": "form-control"}),
            "rate": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "hsn_sac": forms.TextInput(attrs={"class": "form-control"}),
            "default_tax": forms.Select(attrs={"class": "form-select"}),
            "default_unit": forms.Select(attrs={"class": "form-select"}),
        }        