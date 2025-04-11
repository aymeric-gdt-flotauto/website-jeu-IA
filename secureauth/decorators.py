from functools import wraps
from django.shortcuts import redirect
from django.urls import reverse

def login_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if 'user_id' not in request.session:
            return redirect('/auth/login/')
        return view_func(request, *args, **kwargs)
    return _wrapped_view 