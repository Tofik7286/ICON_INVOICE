from django import template

register = template.Library()

@register.filter
def any_item_has_discount(items):
    return any(getattr(item, 'discount_percent', 0) and float(item.discount_percent) != 0 for item in items)

@register.filter
def cartons_for_item(item):
    """Return cartons for an item using rule: 12 DOZ = 1 carton.
    If unit is DOZ, cartons = quantity / 12. Else, return None.
    """
    try:
        unit_label = getattr(getattr(item, 'unit', None), 'label', None)
        qty = getattr(item, 'quantity', None)
        if unit_label and qty:
            if str(unit_label).upper() == 'DOZ':
                return float(qty) / 12.0
    except Exception:
        pass
    return None

@register.simple_tag
def total_cartons(invoice):
    """Calculate total cartons across all items using 12 DOZ = 1 carton."""
    total = 0.0
    try:
        for item in invoice.items.all():
            unit_label = getattr(getattr(item, 'unit', None), 'label', None)
            qty = getattr(item, 'quantity', None)
            if unit_label and qty and str(unit_label).upper() == 'DOZ':
                total += float(qty) / 12.0
    except Exception:
        return 0
    # Return integer if whole number, else float
    return int(total) if total.is_integer() else total
