from django.shortcuts import render, redirect
from .models import User, Profile
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from .decorators import login_required
import re
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os

# Create your views here.

def register(request):
    # Si le formulaire est soumis, on enregistre l'utilisateur.
    if request.method == 'POST':
        # Vérifier si la requête est en AJAX
        is_ajax = request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest' or request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        # Le formulaire demande pseudonym, email et mot de passe.
        pseudonym = request.POST.get('pseudonym', '')
        email = request.POST.get('email', '')
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        
        # Dictionnaire pour stocker les erreurs
        errors = {}
        
        # On vérifie que les mots de passe correspondent.
        if password != confirm_password:
            errors['confirm_password'] = 'Les mots de passe ne correspondent pas.'
        
        # On vérifie que le pseudonyme est valide.
        if len(pseudonym) < 5:
            errors['pseudonym'] = 'Le pseudonyme doit contenir au moins 5 caractères.'
        elif not re.match('^[a-zA-Z]+$', pseudonym):
            errors['pseudonym'] = 'Le pseudonyme ne doit contenir que des lettres (sans chiffres).'
        
        # On vérifie que l'email est valide.
        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
            errors['email'] = 'L\'email est invalide.'
        
        # Vérifier si le pseudonyme ou l'email existe déjà
        if User.objects.filter(pseudonym=pseudonym).exists():
            errors['pseudonym'] = 'Ce pseudonyme est déjà utilisé.'
            
        if User.objects.filter(email=email).exists():
            errors['email'] = 'Cet email est déjà utilisé.'
        
        # S'il y a des erreurs, on les renvoie
        if errors:
            if is_ajax:
                return JsonResponse({'success': False, 'errors': errors})
            else:
                # Pour les navigateurs qui ne supportent pas AJAX
                for field, error in errors.items():
                    messages.error(request, error)
                return render(request, 'registration/register.html')
        
        # Si tout est bon, on enregistre l'utilisateur
        user = User.create_user(pseudonym, email, password)
        user.save()
        
        # On enregistre le profil.
        profile = Profile.objects.create(user=user)
        profile.save()
        
        if is_ajax:
            return JsonResponse({'success': True, 'message': 'Votre compte a été créé avec succès.', 'redirect': '/'})
        else:
            messages.success(request, 'Votre compte a été créé avec succès.')
            return redirect('/')
    
    # Si le formulaire n'est pas soumis, on affiche le formulaire.
    return render(request, 'registration/register.html')

def login_view(request):
    if request.method == 'POST':
        pseudonym = request.POST.get('pseudonym', '')
        password = request.POST.get('password', '')
        
        # Vérifier si l'utilisateur existe
        try:
            user = User.objects.get(pseudonym=pseudonym)
            
            # Vérifier si le compte est verrouillé
            if user.is_account_locked():
                minutes_left = int((user.locked_until - timezone.now()).total_seconds() // 60) + 1
                messages.error(request, f'Compte temporairement bloqué. Réessayez dans {minutes_left} minute(s).')
                return render(request, 'registration/login.html')
            
            # Vérifier le mot de passe
            if user.check_password(password):
                # Authentification réussie, réinitialiser les tentatives de connexion
                user.reset_login_attempts()
                
                # Mettre l'utilisateur en session
                request.session['user_id'] = user.id
                
                # Rediriger vers le changement de mot de passe si nécessaire
                if hasattr(user, 'profile') and user.profile.must_change_password:
                    return redirect('/auth/change-password/')
                else:
                    return redirect('/')
            else:
                # Mot de passe incorrect, incrémenter les tentatives de connexion
                user.increment_login_attempts()
                
                if user.is_account_locked():
                    messages.error(request, 'Trop de tentatives échouées. Compte bloqué pour 2 minutes.')
                else:
                    remaining_attempts = 3 - user.login_attempts
                    if remaining_attempts > 0:
                        messages.error(request, f'Mot de passe incorrect. Il vous reste {remaining_attempts} tentative(s).')
                    else:
                        messages.error(request, 'Mot de passe incorrect. Compte bloqué pour 2 minutes.')
                return render(request, 'registration/login.html')
                
        except User.DoesNotExist:
            messages.error(request, 'Identifiants invalides.')
            return render(request, 'registration/login.html')
    
    return render(request, 'registration/login.html')

@login_required
def change_password(request):
    user = User.objects.get(id=request.session['user_id'])
    
    if request.method == 'POST':
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        if password != confirm_password:
            messages.error(request, 'Les mots de passe ne correspondent pas.')
            return render(request, 'registration/change_password.html')
        
        user.set_password(password)
        
        # Mise à jour du profil pour indiquer que le mot de passe a été modifié
        if hasattr(user, 'profile'):
            user.profile.must_change_password = False
            user.profile.save()
        
        user.save()
        messages.success(request, 'Mot de passe modifié avec succès.')
        return redirect('/auth/profile/')
        
    return render(request, 'registration/change_password.html')

@login_required
def my_profile(request):
    user = User.objects.get(id=request.session['user_id'])
    
    # Récupérer ou créer le profil si nécessaire
    profile, created = Profile.objects.get_or_create(user=user)
    
    # Traiter la requête POST (upload de photo)
    if request.method == 'POST' and request.FILES.get('profile_picture'):
        # Récupérer la photo uploadée
        profile_picture = request.FILES.get('profile_picture')
        
        # Vérifier la taille du fichier (max 5 Mo)
        if profile_picture.size > 5 * 1024 * 1024:
            messages.error(request, 'Le fichier est trop volumineux. Taille maximale : 5 Mo.')
            return redirect('/auth/profile/')
        
        # Vérifier le type de fichier
        allowed_types = ['image/jpeg', 'image/png', 'image/gif']
        if profile_picture.content_type not in allowed_types:
            messages.error(request, 'Format de fichier non supporté. Formats acceptés : JPG, PNG, GIF.')
            return redirect('/auth/change-password/')
        
        # Supprimer l'ancienne image si elle existe
        if user.profile_picture:
            if os.path.isfile(user.profile_picture.path):
                os.remove(user.profile_picture.path)
        
        # Enregistrer la nouvelle image
        filename = f'profile_pictures/{user.id}_{profile_picture.name}'
        user.profile_picture = filename
        path = default_storage.save(filename, ContentFile(profile_picture.read()))
        user.save()
        
        messages.success(request, 'Photo de profil mise à jour avec succès.')
        return redirect('/auth/profile/')
        
    profile_picture = profile.profile_picture if profile else None
        
    return render(request, 'registration/my_profile.html', {
        'pseudonym': user.pseudonym,
        'email': user.email,
        'profile_picture': profile_picture
    })

def logout(request):
    if 'user_id' in request.session:
        del request.session['user_id']
    return redirect('/auth/login/')

def home(request):
    # Vérifier si l'utilisateur est connecté
    if 'user_id' not in request.session:
        return redirect('/auth/login/')
        
    try:
        user = User.objects.get(id=request.session['user_id'])
    except User.DoesNotExist:
        return redirect('/auth/login/')
        
    return render(request, 'home.html', {'user': user})