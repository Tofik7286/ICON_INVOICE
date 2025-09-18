from django import template

register = template.Library()

@register.filter
def any_item_has_discount(items):
    return any(getattr(item, 'discount_percent', 0) and float(item.discount_percent) != 0 for item in items)
