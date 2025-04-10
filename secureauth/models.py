from django.db import models
import re
from django.urls import reverse
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
import datetime

# Create your models here.
class User(models.Model):
    """
    Modèle d'utilisateur personnalisé pour l'authentification sécurisée.
    Gère les tentatives de connexion et le verrouillage temporaire du compte.
    """
    pseudonym = models.CharField(max_length=255, unique=True, 
                                 help_text="Pseudonyme unique (min. 5 caractères, sans chiffres)")
    email = models.EmailField(max_length=255, unique=True, 
                              help_text="Adresse email unique")
    password = models.CharField(max_length=255, 
                               help_text="Mot de passe haché")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    login_attempts = models.IntegerField(default=0, 
                                        help_text="Nombre de tentatives de connexion échouées")
    last_failed_login = models.DateTimeField(null=True, blank=True, 
                                            help_text="Date et heure de la dernière tentative échouée")
    locked_until = models.DateTimeField(null=True, blank=True, 
                                       help_text="Date et heure jusqu'à laquelle le compte est verrouillé")
    
    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.pseudonym
    
    def is_valid_pseudonym_instance(self):
        """
        Vérifie si le pseudonyme de l'instance est valide.
        Un pseudonyme valide doit avoir au moins 5 caractères et ne pas contenir de chiffres.
        """
        return len(self.pseudonym) >= 5 and not any(char.isdigit() for char in self.pseudonym)
    
    @classmethod
    def is_valid_pseudonym(cls, pseudonym):
        """
        Vérifie si un pseudonyme donné est valide.
        Un pseudonyme valide doit avoir au moins 5 caractères et ne pas contenir de chiffres.
        """
        return len(pseudonym) >= 5 and not any(char.isdigit() for char in pseudonym)
    
    def is_valid_email_instance(self):
        """
        Vérifie si l'email de l'instance est valide.
        """
        return self.is_valid_email(self.email)
    
    @classmethod
    def is_valid_email(cls, email):
        """
        Vérifie si un email donné est valide selon un format standard.
        """
        return re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email) is not None
    
    @classmethod
    def create_user(cls, pseudonym, email, password):
        """
        Crée un nouvel utilisateur avec le pseudonyme, l'email et le mot de passe donnés.
        Le mot de passe est automatiquement haché.
        """
        user = cls(pseudonym=pseudonym, email=email, password=make_password(password))
        return user
    
    def check_password(self, raw_password):
        """
        Vérifie si le mot de passe fourni correspond au mot de passe haché de l'utilisateur.
        """
        return check_password(raw_password, self.password)
        
    def set_password(self, raw_password):
        """
        Définit un nouveau mot de passe pour l'utilisateur en le hachant.
        """
        self.password = make_password(raw_password)
        
    def is_account_locked(self):
        """
        Vérifie si le compte de l'utilisateur est actuellement verrouillé.
        """
        if self.locked_until and self.locked_until > timezone.now():
            return True
        return False
    
    def increment_login_attempts(self):
        """
        Incrémente le compteur de tentatives de connexion échouées.
        Verrouille le compte après 3 tentatives échouées.
        """
        self.login_attempts += 1
        self.last_failed_login = timezone.now()
        
        if self.login_attempts >= 3:
            self.locked_until = timezone.now() + datetime.timedelta(minutes=2)
            
        self.save()
        
    def reset_login_attempts(self):
        """
        Réinitialise le compteur de tentatives de connexion échouées.
        Déverrouille le compte.
        """
        self.login_attempts = 0
        self.last_failed_login = None
        self.locked_until = None
        self.save()

class Profile(models.Model):
    """
    Profil utilisateur lié au modèle User.
    Contient des informations supplémentaires comme la photo de profil et 
    la gestion du changement de mot de passe obligatoire.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True,
                                       help_text="Photo de profil de l'utilisateur")
    must_change_password = models.BooleanField(default=True,
                                             help_text="Indique si l'utilisateur doit changer son mot de passe à la prochaine connexion")

    class Meta:
        verbose_name = "Profil"
        verbose_name_plural = "Profils"

    def __str__(self):
        return f"Profil de {self.user.pseudonym}"
    
    def get_absolute_url(self):
        """
        Retourne l'URL vers le détail du profil.
        """
        return reverse('profile_detail', kwargs={'pk': self.pk})

    def is_password_expired(self):
        """
        Vérifie si le mot de passe doit être changé.
        """
        return self.must_change_password
    
    
    
    
    
    
