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
        print("[DEBUG] POST data:", request.POST)
        print("[DEBUG] Form valid:", form.is_valid())
        print("[DEBUG] Formset valid:", formset.is_valid())
        if not formset.is_valid():
            print("[DEBUG] Formset errors:", formset.errors)
            print("[DEBUG] Formset non-form errors:", formset.non_form_errors())
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

    company = Company.objects.first()
    html_string = render_to_string(
        "invoices/pdf_template.html",
        {"invoice": invoice, "company": company}
    )

    # ✅ Generate PDF in-memory (no saving to media folder)
    html = HTML(string=html_string, base_url=request.build_absolute_uri("/"))
    pdf_bytes = html.write_pdf()

    # ✅ Direct download
    pdf_file_name = f"{invoice.invoice_number}_{invoice.pk}.pdf"
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{pdf_file_name}"'

    # ✅ Optional: audit log only (no file save)
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
