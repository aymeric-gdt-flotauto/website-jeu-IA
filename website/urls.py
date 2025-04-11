"""
URL configuration for website project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic.base import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("gameforge.urls")),  # Mettre gameforge en premier pour la page d'accueil
    path("auth/", include("secureauth.urls")),  # Déplacer secureauth sous /auth/
    
    # Redirections pour les anciennes URLs
    path("login/", RedirectView.as_view(url='/auth/login/'), name="login_redirect"),
    path("logout/", RedirectView.as_view(url='/auth/logout/'), name="logout_redirect"),
    path("register/", RedirectView.as_view(url='/auth/register/'), name="register_redirect"),
    path("profile/", RedirectView.as_view(url='/auth/profile/'), name="profile_redirect"),
    path("change-password/", RedirectView.as_view(url='/auth/change-password/'), name="change_password_redirect"),
]

# Ajout des fichiers média pour les images de profil
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
