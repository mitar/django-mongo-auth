from django.middleware import locale
from django.utils import translation

class UserBasedLocaleMiddleware(locale.LocaleMiddleware):
    """
    This middleware will set language based on user's setting.
    """

    def process_request(self, request):
        language = request.user.language
        translation.activate(language)
        request.LANGUAGE_CODE = translation.get_language()
        return None
