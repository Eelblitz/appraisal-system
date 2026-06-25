from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """
    Allows dictionary lookup with a variable key in templates.

    Usage: {{ my_dict|get_item:variable_key }}

    Why do we need this?
    Django templates cannot do {{ dict[variable] }} like Python.
    This custom filter enables: {{ existing_ratings|get_item:aspect.id }}
    Which returns the saved rating for that aspect if it exists.
    """
    if dictionary is None:
        return None
    return dictionary.get(key)