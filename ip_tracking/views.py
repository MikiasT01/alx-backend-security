from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from ratelimit.decorators import ratelimit

@ratelimit(key='ip', rate='10/m', block=True, method='GET', group='authenticated')
@login_required
def login_view(request):
        return HttpResponse("Login successful (authenticated)")

@ratelimit(key='ip', rate='5/m', block=True, method='GET', group='anonymous')
def login_view_anonymous(request):
        return HttpResponse("Login attempt (anonymous)")