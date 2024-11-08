from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.utils import timezone


class AutoLogoutMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.user.is_authenticated:
            # If the session has expired, mark the user as logged out
            if not request.session.get('has_expired', False):
                session_key = request.session.session_key
                session = Session.objects.get(session_key=session_key)
                session_expiry = session.expire_date
                if session_expiry <= timezone.now():
                    request.user.is_logged_in = False
                    request.user.save()
                    request.session['has_expired'] = True