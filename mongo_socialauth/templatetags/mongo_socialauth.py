from django import template

register = template.Library()

@register.inclusion_tag('user/user_image.html', takes_context=True)
def user_image(context, user=None):
    if user is None:
        user = context.get('user')

    if user:
        return {
            'user_image_url': user.get_image_url(),
        }

    return {}
