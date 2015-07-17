########################################################################################################################
# VECNet CI - Prototype
# Date: 4/5/2013
# Institution: University of Notre Dame
# Primary Authors:
########################################################################################################################
from django import template

register = template.Library()

@register.inclusion_tag('lib/tags/notifications.html', takes_context=True)
def show_notifications(context):
    # TODO Add function docstring
    # Retrieve the session
    try: #try/except is needed for the server error (500) view to function
        session = context["request"].session
        if session.__contains__('notifications'):
            notifications = session.pop('notifications')
            return {'notifications':notifications}
        else:
            return {'notifications':set()}
    except:
        pass

class Notification:
    # TODO Add class docstring
    #Represent a notification
    SUCCESS = "alert-success"
    ERROR = "alert-error"
    ALERT = "alert"
    INFO = "alert-info"

    def __init__(self):
        self.type = ""
        self.message = ""


def set_notification(notification_type,message,session):
    # TODO Add function docstring
    notification = Notification()
    notification.message = message
    notification.type = notification_type
    # Save in sessions
    if not session.__contains__("notifications"):
        session["notifications"] = set()
    session["notifications"].add(notification)
