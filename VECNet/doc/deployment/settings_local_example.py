# APP_ENV should be switched to production
APP_ENV = "production"

# Disable DEBUG
DEBUG = False
# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
# Replace ci.vecnet.org with actual hostname
ALLOWED_HOSTS = ["ci.vecnet.org"]

# Specify django log file.
LOG_FILE = "/var/log/django/ci.vecnet.org.django.log"

# Configure database parameters
#DATAWAREHOUSE_HOST =
#DATAWAREHOUSE_USER =
#DATAWAREHOUSE_PASSWORD =

#Configure login and logout page for SSO
LOGIN_URL = "https://www.vecnet.org/index.php/login-register"
LOGOUT_URL = "https://www.vecnet.org/index.php/log-out"
# The name of the GET field which contains the URL to redirect to after login
# By default, Django uses "next" and auth_pubtkt uses "back"
REDIRECT_FIELD_NAME = "back"

# Email host
EMAIL_HOST = "smtp.nd.edu"
EMAIL_PORT = 25
EMAIL_USE_TLS = True
SERVER_EMAIL = "ci@ci.vecnet.org"

# Enable mod_auth_pubtkt support
AUTHENTICATION_BACKENDS = (
     'django.contrib.auth.backends.RemoteUserBackend',
)
from settings import MIDDLEWARE_CLASSES
MIDDLEWARE_CLASSES += (
    'django.contrib.auth.middleware.RemoteUserMiddleware',
)

# Optional parameters
#DATAWAREHOSE_DW_NAME = "dw"
#DATAWAREHOSE_PORT = 5432

