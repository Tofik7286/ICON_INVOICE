from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse, Http404
from django.template.loader import render_to_string
from django.core.paginator import Paginator
from django.utils import timezone
import os
from .models import *
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm, CustomLoginForm
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render
from .models import CustomUser
from .forms import *
from weasyprint import HTML

from .forms import InvoiceForm, InvoiceItemFormSet
from .models import (
    Invoice, InvoiceItem, InvoiceSequence,
    InvoiceAudit, Company
)
from django.shortcuts import redirect

def root_redirect(request):
    return redirect("accounts:login")


# ----------------------
# Helper: Create invoice number atomically
# ----------------------
def _generate_invoice_number(seq_no, date):
    seq_str = str(seq_no).zfill(4)  # 0001
    return f"INV_{seq_str}_{date.strftime('%Y%m%d')}"

# sirf staff/admin users ko access mile
@user_passes_test(lambda u: u.is_staff)
def user_list(request):
    users = CustomUser.objects.all()
    return render(request, "users/list.html", {"users": users})
# ----------------------
# Create Invoice
# ----------------------
@login_required
def invoice_create(request):
    if request.method == "POST":
        form = InvoiceForm(request.POST)
        formset = InvoiceItemFormSet(request.POST, prefix="items")  # ✅ prefix added
        # print("[DEBUG] POST data:", request.POST)
        # print("[DEBUG] Form valid:", form.is_valid())
        # print("[DEBUG] Formset valid:", formset.is_valid())
        # if not formset.is_valid():
            # print("[DEBUG] Formset errors:", formset.errors)
            # print("[DEBUG] Formset non-form errors:", formset.non_form_errors())
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                # Sequence locking
                seq, _ = InvoiceSequence.objects.select_for_update().get_or_create(pk=1)
                seq.last_number += 1
                seq_no = seq.last_number
                seq.save()

                invoice = form.save(commit=False)
                invoice.seq_number = seq_no
                invoice.invoice_number = _generate_invoice_number(seq_no, invoice.date)
                invoice.created_by = request.user

                # GST logic: IGST if from_party.state != to_party.state
                if invoice.apply_gst:
                    invoice.is_igst = (invoice.from_party.state != invoice.to_party.state)

                invoice.save()
                
                items = formset.save(commit=False)
                for item in items:
                    if item.product:
                        item.rate = item.product.rate  
                    item.invoice = invoice
                    item.save()
                formset.save_m2m()

                # Link items
                formset.instance = invoice
                formset.save()
                print("[DEBUG] Saved items:", list(invoice.items.all()))

                # Audit log
                InvoiceAudit.objects.create(
                    invoice=invoice,
                    user=request.user,
                    action="created",
                    note=f"Invoice {invoice.invoice_number} created."
                )

                return redirect("invoices:preview", pk=invoice.pk)
    else:
        form = InvoiceForm(initial={"date": timezone.localdate()})
        formset = InvoiceItemFormSet(prefix="items")  # ✅ prefix added

    # ✅ Send product data for JS auto-fill
    products = Product.objects.values(
        "id",
        "hsn_sac",
        "rate",
        "default_unit_id",       # 👈 fixed
        "default_unit__label",
    )

    return render(
        request,
        "invoices/create.html",
        {
            "form": form,
            "formset": formset,
            "products": list(products),  # json_script handle karega
        },
    )

# ----------------------
# Preview Invoice
# ----------------------
@login_required
def invoice_preview(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk, is_deleted=False)

    if not request.user.is_staff and invoice.created_by != request.user:
        raise Http404("Not allowed")

    company = Company.objects.first()
    print("[DEBUG] Previewing invoice:", invoice)
    print("[DEBUG] Items in preview:", list(invoice.items.all()))
    return render(request, "invoices/preview.html", {"invoice": invoice, "company": company})

# ----------------------
# Generate PDF
# ----------------------
from django.conf import settings

@login_required
def invoice_generate_pdf(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk, is_deleted=False)
    
    if not (request.user.is_staff or invoice.created_by == request.user):
        raise Http404("Not allowed")

    
    from_party = invoice.from_party  

    html_string = render_to_string(
        "invoices/pdf_template.html",
        {"invoice": invoice, "from_party": from_party}   # 👈 yaha change
    )

    html = HTML(string=html_string, base_url=request.build_absolute_uri("/"))
    pdf_bytes = html.write_pdf()

    pdf_file_name = f"{invoice.invoice_number}_{invoice.pk}.pdf"
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{pdf_file_name}"'

    InvoiceAudit.objects.create(
        invoice=invoice,
        user=request.user,
        action="pdf_generated",
        note=f"PDF generated (not stored on disk)"
    )

    return response

# ----------------------
# Invoice List (with search & pagination)
# ----------------------
@login_required
def invoice_list(request):
    qs = Invoice.objects.filter(is_deleted=False)

    # Normal user → sirf apne invoices
    if not request.user.is_staff:
        qs = qs.filter(created_by=request.user)

    search = request.GET.get("q")
    if search:
        qs = qs.filter(invoice_number__icontains=search) | qs.filter(from_party__name__icontains=search) | qs.filter(to_party__name__icontains=search)

    paginator = Paginator(qs, 25)
    invoices = paginator.get_page(request.GET.get("page", 1))
    return render(request, "invoices/list.html", {"invoices": invoices})


# ----------------------
# Soft Delete
# ----------------------
@login_required
def invoice_delete(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)

    if not request.user.is_staff and invoice.created_by != request.user:
        raise Http404("Not allowed")

    invoice.is_deleted = True
    invoice.save()

    InvoiceAudit.objects.create(invoice=invoice, user=request.user, action="deleted", note="Invoice soft-deleted")
    return redirect("invoices:list")

def register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("invoices:list")
    else:
        form = CustomUserCreationForm()
    return render(request, "auth/register.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        form = CustomLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("invoices:list")
    else:
        form = CustomLoginForm()
    return render(request, "auth/login.html", {"form": form})


@login_required
def logout_view(request):
    logout(request)
    return redirect("accounts:login")

# ----------------------
# Update Invoice
# ----------------------
@login_required
@login_required
def invoice_update(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk, is_deleted=False)

    if not request.user.is_staff and invoice.created_by != request.user:
        raise Http404("You are not allowed to edit this invoice.")

    if request.method == "POST":
        form = InvoiceForm(request.POST, instance=invoice)
        formset = InvoiceItemFormSet(request.POST, instance=invoice, prefix="items")

        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                updated_invoice = form.save(commit=False)
                
                if updated_invoice.apply_gst:
                    updated_invoice.is_igst = (updated_invoice.from_party.state != updated_invoice.to_party.state)
                else:
                    updated_invoice.is_igst = False
                updated_invoice.save()

                # ---- START: YAHAN PAR CHANGE HAI ----
                
                # Pehle formset ko save karein taaki existing items update ho jayein
                # aur naye items create ho jayein (bina rate ke)
                items = formset.save(commit=False)
                
                # Ab har item par loop karke rate set karein
                for item in items:
                    # Agar item naya hai aur product select kiya hai
                    if item.product and not item.rate:
                        item.rate = item.product.rate
                    item.invoice = updated_invoice
                    item.save() # Ab item ko save karein
                
                formset.save_m2m() # ManyToMany fields ke liye (agar ho toh)

                # ---- END: CHANGE KHATAM ----

                InvoiceAudit.objects.create(
                    invoice=invoice,
                    user=request.user,
                    action="updated",
                    note=f"Invoice {invoice.invoice_number} updated."
                )
                return redirect("invoices:preview", pk=invoice.pk)
    else:
        form = InvoiceForm(instance=invoice)
        formset = InvoiceItemFormSet(instance=invoice, prefix="items")
        
    products = Product.objects.values(
        "id", "hsn_sac", "rate", "default_unit_id", "default_unit__label"
    )

    return render(
        request,
        "invoices/update.html",
        {
            "form": form,
            "formset": formset,
            "invoice": invoice,
            "products": list(products),
        },
    )
    invoice = get_object_or_404(Invoice, pk=pk, is_deleted=False)

    # Permission check: Sirf staff ya creator hi edit kar sakta hai
    if not request.user.is_staff and invoice.created_by != request.user:
        raise Http404("You are not allowed to edit this invoice.")

    if request.method == "POST":
        form = InvoiceForm(request.POST, instance=invoice)
        formset = InvoiceItemFormSet(request.POST, instance=invoice, prefix="items")

        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                # GST logic update
                updated_invoice = form.save(commit=False)
                if updated_invoice.apply_gst:
                    updated_invoice.is_igst = (updated_invoice.from_party.state != updated_invoice.to_party.state)
                else:
                    updated_invoice.is_igst = False
                updated_invoice.save()

                # Save formset
                formset.save()

                # Audit log
                InvoiceAudit.objects.create(
                    invoice=invoice,
                    user=request.user,
                    action="updated",
                    note=f"Invoice {invoice.invoice_number} updated."
                )
                return redirect("invoices:preview", pk=invoice.pk)
    else:
        form = InvoiceForm(instance=invoice)
        formset = InvoiceItemFormSet(instance=invoice, prefix="items")
        
    products = Product.objects.values(
        "id", "hsn_sac", "rate", "default_unit_id", "default_unit__label"
    )

    return render(
        request,
        "invoices/update.html", # Hum yeh template abhi banayenge
        {
            "form": form,
            "formset": formset,
            "invoice": invoice,
            "products": list(products),
        },
    )



# ----------------------
# Party CRUD Views
# ----------------------

@login_required
def party_list(request):
    parties = Party.objects.all()
    return render(request, "parties/list.html", {"parties": parties})

@login_required
def party_create(request):
    if request.method == "POST":
        form = PartyForm(request.POST)
        if form.is_valid():
            party = form.save(commit=False)
            party.created_by = request.user
            party.save()
            return redirect("parties:list")
    else:
        form = PartyForm()
    return render(request, "parties/form.html", {"form": form})

@login_required
def party_update(request, pk):
    party = get_object_or_404(Party, pk=pk)
    if request.method == "POST":
        form = PartyForm(request.POST, instance=party)
        if form.is_valid():
            form.save()
            return redirect("parties:list")
    else:
        form = PartyForm(instance=party)
    return render(request, "parties/form.html", {"form": form, "party": party})

@login_required
def party_delete(request, pk):
    party = get_object_or_404(Party, pk=pk)
    if request.method == "POST":
        try:
            party.delete()
            return redirect("parties:list")
        except:
            # Agar party kisi invoice se judi hai to delete nahi hogi
            error_message = "This party cannot be deleted because it is linked to one or more invoices."
            return render(request, "parties/confirm_delete.html", {"party": party, "error_message": error_message})
            
    return render(request, "parties/confirm_delete.html", {"party": party})
# ----------------------
# Product CRUD Views
# ----------------------

@login_required
def product_list(request):
    products = Product.objects.all()
    return render(request, "products/list.html", {"products": products})

@login_required
def product_create(request):
    if request.method == "POST":
        # request.FILES ko add karna zaroori hai image upload ke liye
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.created_by = request.user
            product.save()
            return redirect("products:list")
    else:
        form = ProductForm()
    return render(request, "products/form.html", {"form": form})

@login_required
def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        # request.FILES ko yahan bhi add karna zaroori hai
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            return redirect("products:list")
    else:
        form = ProductForm(instance=product)
    return render(request, "products/form.html", {"form": form, "product": product})

@login_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        try:
            product.delete()
            return redirect("products:list")
        except:
            # Agar product kisi invoice item se juda hai to delete nahi hoga
            error_message = "This product cannot be deleted because it is linked to one or more invoices."
            return render(request, "products/confirm_delete.html", {"product": product, "error_message": error_message})
            
    return render(request, "products/confirm_delete.html", {"product": product})