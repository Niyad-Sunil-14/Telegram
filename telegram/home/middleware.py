from django.utils.timezone import now
from . models import User

class UpdateLastActivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        member: User = request.user
        if member.is_authenticated:
            member.last_seen = now()
            member.save()

        return response
    
