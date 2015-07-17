from django import http
from django.shortcuts import render, redirect
from django.template import (loader, TemplateDoesNotExist)
from django.views.decorators.csrf import requires_csrf_token
from django.core.urlresolvers import reverse
from lib.templatetags.base_extras import set_notification
import smtplib
from datetime import datetime
from django.conf import settings
import json

@requires_csrf_token
def view_server_error(request, template_name='500.html'):
    """
    500 error handler.

    Templates: :template:`500.html` by default, others expected: '403.html','404.html'
    Context: None
    """
    try:
        loader.get_template(template_name)
    except TemplateDoesNotExist:
        return http.HttpResponseServerError('<h1>Server Error - Template Not Found</h1>')

    context = {'STATIC_URL': '/static/'}
    if template_name == "500.html":
        status = 500
    if template_name == "403.html":
        status = 403
    if template_name == "404.html":
        status = 404

    return render(request, template_name, context, status = status)

@requires_csrf_token
def error_submit(request):

    try:
        sender_email = settings.SERVER_EMAIL
        server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
        if getattr(settings, 'EMAIL_USE_TLS', True):
            server.starttls()
        to = ''
        for recipient in settings.ADMINS:
            to += recipient[1] + ','

        header = 'To:' + to + '\n' + 'From: ' + sender_email + '\n' + 'Subject:VecNet Server Error (' + request.POST['error_code'] + ') report from ' + request.POST['name'] + '\n\n'

        msg = header + 'Server Error Form Results: \n\n'
        msg = msg    + 'Error Type: ' + request.POST['error_code'] + '\n'
        msg = msg    + 'Error Reported By: ' + request.POST['name'] + '\n'
        msg = msg    + 'Reporter\'s Email: ' + request.POST['email'] + '\n\n'

        msg = msg    + 'Description of problem: ' + request.POST['rant'] + '\n\n'

        msg = msg    + 'Report timestamp: ' + str(datetime.today()) + '\n\n'
        try:
            msg = msg    + 'Username: ' + request.user.username + '\n\n'
        except:
            pass

        try:
            msg = msg + "User agent: " + request.META['HTTP_USER_AGENT'] + "\n\n"
        except:
            pass

        try:
            msg = msg + "URL: " + request.path_info + "?" + request.META['QUERY_STRING'] + "\n\n"
        except:
            pass

        try:
            msg = msg    + 'Session data: ' + "%s" % request.session.load() + '\n\n'
        except:
            pass
        server.sendmail(sender_email, to, msg)

        server.close()

        set_notification('alert-success', '<strong>Thank you for your submission!</strong> We will resolve this issue as soon as possible.', request.session)
    except:
        set_notification('alert-error', '<strong>Error!</strong> Your response wasn\'t submitted. Please contact us directly at support@vecnet.org for further assistance.', request.session)

    return redirect(reverse('index'))