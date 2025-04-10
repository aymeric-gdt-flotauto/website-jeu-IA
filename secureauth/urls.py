from django.urls import path
from . import views as secureauth_views

urlpatterns = [
    path("", secureauth_views.home, name="home"),
    path("register/", secureauth_views.register, name="register"),
    path("login/", secureauth_views.login_view, name="login"),
    path("logout/", secureauth_views.logout, name="logout"),
    path("profile/", secureauth_views.my_profile, name="my_profile"),
    path("change-password/", secureauth_views.change_password, name="change_password")
]