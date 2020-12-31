from django.template.defaulttags import register


@register.filter
def get_item(dictionary, key):
    try:
        return dictionary[key]
    except ValueError:
        return None


@register.filter
def class_name(value):
    if hasattr(value, "get_real_instance_class"):
        return value.get_real_instance_class().__name__
    return value.__class__.__name__
