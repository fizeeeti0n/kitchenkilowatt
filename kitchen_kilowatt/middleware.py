from django.shortcuts import redirect
from django.conf import settings
from django.urls import resolve

class LoginRequiredMiddleware:
    """
    Middleware that requires a user to be authenticated to view any page other
    than the login/signup pages or the admin backend.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.exempt_urls = [
            '/accounts/login/',
            '/accounts/register/',
            '/accounts/logout/',
        ]

    def __call__(self, request):
        path = request.path_info
        
        # Check if the path is in the exempt list or is an admin path
        is_exempt = any(path.startswith(url) for url in self.exempt_urls) or path.startswith('/admin/') or path.startswith(settings.MEDIA_URL) or path.startswith(settings.STATIC_URL)
        
        if not request.user.is_authenticated and not is_exempt:
            return redirect(f"{settings.LOGIN_URL}?next={path}")
            
        response = self.get_response(request)
        return response
