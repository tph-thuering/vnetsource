from django.conf import settings
from data_services.models import DimUser


def app_env(request):
    """ This function adds value of APP_ENV variable to template context
    It used to define login and logout pages. If we are running in production
    enviroment, use auth_pubtkt. In dev enviroment, use local django auth system
    """

    env = {"APP_ENV": settings.APP_ENV,
            "LOGIN_URL": settings.LOGIN_URL,
            "REDIRECT_FIELD_NAME": getattr(settings, 'REDIRECT_FIELD_NAME', 'next'),
            "LOGOUT_URL": settings.LOGOUT_URL}
    if hasattr(settings, "SERVER_MAINTENANCE_MESSAGE"):
         env["SERVER_MAINTENANCE_MESSAGE"] = settings.SERVER_MAINTENANCE_MESSAGE
    return env


def app_dim_user(request):
    if request.user.is_anonymous():
        return {}
    else:
        return {'dim_user': DimUser.objects.get_or_create(username=request.user.username)[0]}