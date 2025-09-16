from django import forms
from django.forms import inlineformset_factory
from .models import Invoice, InvoiceItem, Party, Product, Unit, Tax


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
            "rate",
            "discount_percent",
        ]
        widgets = {
            "product": forms.Select(attrs={"class": "form-select"}),
            "description": forms.TextInput(attrs={"class": "form-control", "placeholder": "Item description"}),
            "hsn_sac": forms.TextInput(attrs={"class": "form-control"}),
            "unit": forms.Select(attrs={"class": "form-select"}),
            "quantity": forms.NumberInput(attrs={"class": "form-control", "step": "0.001"}),
            "rate": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "discount_percent": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        }


# ----------------------
# Invoice Item Formset
# ----------------------
InvoiceItemFormSet = inlineformset_factory(
    Invoice,
    InvoiceItem,
    form=InvoiceItemForm,
    extra=1,        # by default ek empty row dikhayega
    can_delete=True # allow user to remove rows
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
