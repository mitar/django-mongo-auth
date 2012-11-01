from django import http
from django.utils import translation

from . import forms
from .. import views

def set_language(request):
    """
    Redirect to a given url while setting the chosen language in the user
    setting. The url and the language code need to be specified in the request
    parameters.

    Since this view changes how the user will see the rest of the site, it must
    only be accessed as a POST request. If called as a GET request, it will
    redirect to the page in the request (the 'next' parameter) without changing
    any state.
    """

    next = request.REQUEST.get('next', None)
    if not next:
        next = request.META.get('HTTP_REFERER', None)
    if not next:
        next = '/'
    response = http.HttpResponseRedirect(next)
    if request.method == 'POST':
        lang_code = request.POST.get('language', None)
        if lang_code and translation.check_for_language(lang_code):
            # We reload to make sure user object is recent
            request.user.reload()
            request.user.language = lang_code
            request.user.save()
    return response

class RegistrationView(views.RegistrationView):
    form_class = forms.RegistrationForm

    def object_data(self, form):
        data = super(RegistrationView, self).object_data(form)
        data.update({
            'gender': form.cleaned_data['gender'],
            'birthdate': form.cleaned_data['birthdate'],
        })
        return data

class AccountChangeView(views.AccountChangeView):
    form_class = forms.AccountChangeForm

    def form_valid(self, form):
        user = self.request.user
        user.gender = form.cleaned_data['gender']
        user.birthdate = form.cleaned_data['birthdate']
        return super(AccountChangeView, self).form_valid(form)

    def get_initial(self):
        initial = super(AccountChangeView, self).get_initial()
        initial.update({
            'gender': self.request.user.gender,
            'birthdate': self.request.user.birthdate,
        })
        return initial
