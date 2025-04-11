from django.db import models
from secureauth.models import User
# Create your models here.

class GameIdea(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    genre = models.CharField(max_length=255)  # RPG, FPS, MOBA, Visual Novel, etc. On aura une liste déroulante pour choisir le genre mais on pourra également écrire quelque chose de personnalisé.
    style_graphique = models.CharField(max_length=255)  # 2D, 3D, pixel art, etc. On aura une liste déroulante pour choisir le style graphique mais on pourra également écrire quelque chose de personnalisé.
    ambiance_visuelle = models.CharField(max_length=255)  # Fantasy, Science-fiction, etc. On aura une liste déroulante pour choisir l'ambiance visuelle mais on pourra également écrire quelque chose de personnalisé.
    ambiance_narrative = models.CharField(max_length=255)  # Tragique, comique, etc. On aura une liste déroulante pour choisir l'ambiance narrative mais on pourra également écrire quelque chose de personnalisé.
    mots_cles = models.CharField(max_length=255)  # Guerre, Amour, Trahison, etc. On aura une liste déroulante pour choisir les mots clés mais on pourra également écrire quelque chose de personnalisé.
    reference_culturelle = models.CharField(max_length=255)  # Zelda, Final Fantasy, Dark Souls, etc. On aura une liste déroulante pour choisir la référence culturelle mais on pourra également écrire quelque chose de personnalisé.
    description = models.TextField() # Description du jeu
    created_at = models.DateTimeField(auto_now_add=True)

class GameGeneration(models.Model):
    game_idea = models.ForeignKey(GameIdea, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    univers_de_jeu = models.TextField() # Type, ambiance, style graphique, etc.
    histoire_principale = models.TextField() # Scénario structuré
    personnages = models.TextField() # Avec leur rôle, capacités, motivations, etc.
    illustrations_conceptuelles = models.TextField() # URL d'une illustration conceptuelle
    pitch_deck = models.TextField() # Fiche de présentation du jeu (présentation complète type “pitch deck”)
    created_at = models.DateTimeField(auto_now_add=True)
