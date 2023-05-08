from django import template
from django.utils.safestring import mark_safe
import bleach

register = template.Library()

_ALLOWED_ATTRIBUTES = {
        'a': ['href', 'title'],
        'table': ['class']
}
_ALLOWED_TAGS = ['b', 'i', 'ul', 'li', 'p', 'br', 'a', 'pre','code','h1', 'h2', 'h3', 'h4', 'ol','strong', 'em', 'blockquote',
    'table', 'thead', 'tr', 'td', 'tbody', 'th']

@register.filter()
def xsafe(text):
    return mark_safe(bleach.clean(text, tags=_ALLOWED_TAGS, attributes=_ALLOWED_ATTRIBUTES))
