from django import template

register = template.Library()

@register.filter
def get_category_color(category):
    colors = {
        'typing': 'primary',
        'design': 'success',
        'errands': 'warning',
        'academic': 'info',
        'photography': 'danger',
        'tutoring': 'purple',
        'tech': 'dark',
        'writing': 'secondary',
        'other': 'secondary'
    }
    return colors.get(category, 'secondary')

@register.filter
def get_category_icon(category):
    icons = {
        'typing': 'keyboard',
        'design': 'paint-brush',
        'errands': 'running',
        'academic': 'graduation-cap',
        'photography': 'camera',
        'tutoring': 'chalkboard-teacher',
        'tech': 'laptop-code',
        'writing': 'pen-fancy',
        'other': 'ellipsis-h'
    }
    return icons.get(category, 'briefcase')

@register.filter
def split(value, delimiter):
    """Split a string by delimiter"""
    if value:
        return value.split(delimiter)
    return []

@register.filter
def filter_status(applications, status):
    """Filter applications by status"""
    return [app for app in applications if app.status == status]

@register.filter
def first_n(value, n):
    """Get first n items from a list"""
    try:
        return value[:int(n)]
    except (TypeError, ValueError, IndexError):
        return value