from django import template

register = template.Library()


@register.filter
def split(value, delimiter):
    """Split a string by delimiter"""
    if value:
        return value.split(delimiter)
    return []


@register.filter
def file_icon(file_name):
    """Get appropriate icon for file type"""
    extension = file_name.split('.')[-1].lower() if '.' in file_name else ''

    icon_map = {
        'pdf': 'file-pdf',
        'doc': 'file-word',
        'docx': 'file-word',
        'ppt': 'file-powerpoint',
        'pptx': 'file-powerpoint',
        'xls': 'file-excel',
        'xlsx': 'file-excel',
        'txt': 'file-alt',
        'zip': 'file-archive',
        'rar': 'file-archive',
        'jpg': 'file-image',
        'jpeg': 'file-image',
        'png': 'file-image',
        'mp4': 'file-video',
        'mp3': 'file-audio',
    }

    return icon_map.get(extension, 'file')