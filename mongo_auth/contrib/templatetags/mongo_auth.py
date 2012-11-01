from django import template

register = template.Library()

@register.inclusion_tag('mongo_auth/user_image.html', takes_context=True)
def user_image(context, user=None):
    if not user:
        user = context.get('user')

    if not user:
        return {}

    return {
        'user_image_url': user.get_image_url(),
    }
