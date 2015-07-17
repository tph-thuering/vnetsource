from django.http import HttpResponseRedirect
from django.conf import settings
from re import compile
import urllib
from data_services.models import DimUser

EXEMPT_URLS = [compile(settings.LOGIN_URL.lstrip('/'))]
if hasattr(settings, 'LOGIN_EXEMPT_URLS'):
    EXEMPT_URLS += [compile(expr) for expr in settings.LOGIN_EXEMPT_URLS]

class LoginRequiredMiddleware:
    """
    Middleware that requires a user to be authenticated to view any page other
    than LOGIN_URL. Exemptions to this requirement can optionally be specified
    in settings via a list of regular expressions in LOGIN_EXEMPT_URLS (which
    you can copy from your urls.py).

    Requires authentication middleware and template context processors to be
    loaded. You'll get an error if they aren't.

    Origin:
    http://stackoverflow.com/questions/3214589/django-how-can-i-apply-the-login-required-decorator-to-my-entire-site-excludin
    """
    def process_request(self, request):
        redirect_url = settings.LOGIN_URL + '?next=%s' % urllib.quote(request.build_absolute_uri())
        is_authenticated = request.user.is_authenticated() if hasattr(request, "user") else False

        if not is_authenticated:
            path = request.path_info.lstrip('/')
            if not any(m.match(path) for m in EXEMPT_URLS):
                return HttpResponseRedirect(redirect_url)

class CreateDimUserMiddleware:
    """
    Middleware that creates DimUser object for current user if it does not exist yet
    """
    def process_request(self, request):
        is_authenticated = request.user.is_authenticated() if hasattr(request, "user") else False

        if is_authenticated:
            DimUser.objects.get_or_create(username=request.user.username)
