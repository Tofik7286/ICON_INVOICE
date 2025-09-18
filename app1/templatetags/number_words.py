# invoices/templatetags/number_words.py
from django import template
from num2words import num2words

register = template.Library()

@register.filter
def amount_to_words(value):
    """Convert numeric amount into words in English for invoice."""
    try:
        val = float(value)
    except Exception:
        return ""
    rupees = int(val)
    paise = int(round((val - rupees) * 100))

    words = num2words(rupees, lang="en_IN").title() + " Rupees"
    if paise > 0:
        words += f" and {num2words(paise, lang='en_IN').title()} Paise"
    return words + " Only"

@register.filter
def any_item_has_discount(items):
    return any(getattr(item, 'discount_percent', 0) and float(item.discount_percent) != 0 for item in items)
