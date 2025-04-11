from django.shortcuts import render, redirect
from secureauth.models import User
from secureauth.decorators import login_required
from .models import GameIdea, GameGeneration
from dotenv import load_dotenv
import os
from openai import OpenAI
import json
import pprint
from django.db.models import Q

# Chargement des variables d'environnement

load_dotenv()
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Fonctions utilitaires

def api_call_text_generation(prompt): # fonction utilitaire
    """Appelle l'API de GPT-4o-mini pour générer un texte"""
    response = client.responses.create(
        model="gpt-4o-mini",
        input=prompt
    )

    return response.output_text


def api_call_image_generation(prompt):
    """Appelle l'API de DALL·E 2 pour générer une image"""
    response = client.images.generate(
        model="dall-e-2",
        prompt=prompt
    )

    return response.data[0].url

def generate_game_generation(game_idea): # fonction utilitaire
    TEXT_GENERATION_PROMPT = """
titre: {title},
genre: {genre},
style_graphique: {style_graphique},
ambiance_visuelle: {ambiance_visuelle},
ambiance_narrative: {ambiance_narrative},
mots_cles: {mots_cles},
reference_culturelle: {reference_culturelle},
description: {description}
"""
    END_PROMPT = """
à partir de ces informations, amuse toi à décrire l'univers d'un jeu (type, ambiance, style graphique), 
l'histoire (Scénario structuré), 
des personnages (Avec leur rôle, capacités, motivations, etc...), 
un prompt pour une illustration conceptuelle à destination de DALL-E (en anglais), 
ainsi qu'un court résumé du jeu. Ta réponse doit être sous forme de json.
Description du json attendu : 
-'histoire':{'scenario':[{'chapitre':int, 'description':str, 'titre':str}], 'titre':str}
-'illustration_prompt':str
-'personnages':[{'nom':str, 'role':str, 'capacites':[str], 'motivations':str}]
-'resume':str
- 'univers':{'type':str, 'ambiance':str, 'mots_cles':[str], 'inspiration':str, 'thème':str, 'style_graphique':str}
"""
    
    try:
        prompt = TEXT_GENERATION_PROMPT.format(title=game_idea.title, 
                                               genre=game_idea.genre, 
                                               style_graphique=game_idea.style_graphique, 
                                               ambiance_visuelle=game_idea.ambiance_visuelle, 
                                               ambiance_narrative=game_idea.ambiance_narrative, 
                                               mots_cles=game_idea.mots_cles, 
                                               reference_culturelle=game_idea.reference_culturelle, 
                                               description=game_idea.description
                                            ) + END_PROMPT
        
        response = api_call_text_generation(prompt)
        response = response.replace("```json", "").replace("```", "")
        
        # Parser le json
        data = json.loads(response)
        
        # Vérifier la présence des clés nécessaires et ajouter des valeurs par défaut si nécessaire
        if 'histoire' not in data:
            data['histoire'] = {
                'titre': 'Histoire principale',
                'scenario': [{'chapitre': 1, 'titre': 'Introduction', 'description': "L'histoire commence..."}]
            }
        
        if 'illustration_prompt' not in data:
            data['illustration_prompt'] = f"A concept art for a {game_idea.genre} game called '{game_idea.title}' with {game_idea.style_graphique} graphic style"
        
        if 'personnages' not in data:
            data['personnages'] = [{'nom': 'Personnage principal', 'role': 'Protagoniste', 'capacites': ['Adaptabilité'], 'motivations': 'Découvrir le monde'}]
            
        if 'resume' not in data:
            data['resume'] = f"Un jeu {game_idea.genre} avec un style graphique {game_idea.style_graphique}."
            
        if 'univers' not in data:
            data['univers'] = {
                'type': game_idea.genre,
                'ambiance': game_idea.ambiance_visuelle,
                'style_graphique': game_idea.style_graphique,
                'mots_cles': [game_idea.mots_cles.split(',')[0].strip()]
            }
        
        # Générer l'illustration
        data['illustration_url'] = api_call_image_generation(data['illustration_prompt'])
        
        # Standardiser le format et transformer en chaînes JSON
        result = {
            'histoire': json.dumps(data['histoire'], ensure_ascii=False),
            'personnages': json.dumps(data['personnages'], ensure_ascii=False),
            'univers': json.dumps(data['univers'], ensure_ascii=False),
            'illustration_url': data['illustration_url'],
            'resume': data['resume']
        }
        
        return result
        
    except Exception as e:
        print(f"Erreur lors de la génération: {e}")
        # En cas d'erreur, créer une structure par défaut
        default_data = {
            'histoire': json.dumps({
                'titre': 'Histoire principale',
                'scenario': [{'chapitre': 1, 'titre': 'Introduction', 'description': "L'histoire commence..."}]
            }, ensure_ascii=False),
            'personnages': json.dumps([
                {'nom': 'Personnage principal', 'role': 'Protagoniste', 'capacites': ['Adaptabilité'], 'motivations': 'Découvrir le monde'}
            ], ensure_ascii=False),
            'univers': json.dumps({
                'type': game_idea.genre,
                'ambiance': game_idea.ambiance_visuelle,
                'style_graphique': game_idea.style_graphique,
                'mots_cles': [game_idea.mots_cles.split(',')[0].strip()]
            }, ensure_ascii=False),
            'illustration_prompt': f"A concept art for a {game_idea.genre} game called '{game_idea.title}' with {game_idea.style_graphique} graphic style"
        }
        
        # Tenter de générer une illustration même en cas d'erreur
        try:
            default_data['illustration_url'] = api_call_image_generation(default_data['illustration_prompt'])
        except:
            default_data['illustration_url'] = ""
            
        default_data['resume'] = f"Un jeu {game_idea.genre} avec un style graphique {game_idea.style_graphique}."
        
        return default_data

def format_game_generation_for_template(game_generation):
    """Prépare les données de GameGeneration pour l'affichage dans le template"""
    formatted_data = {}
    
    # Essayer de parser l'univers JSON
    try:
        formatted_data['univers'] = json.loads(game_generation.univers_de_jeu)
    except:
        formatted_data['univers'] = {"type": "Information non disponible"}
    
    # Essayer de parser l'histoire JSON
    try:
        formatted_data['histoire'] = json.loads(game_generation.histoire_principale)
    except:
        formatted_data['histoire'] = {"titre": "Histoire", "scenario": []}
    
    # Essayer de parser les personnages JSON
    try:
        formatted_data['personnages'] = json.loads(game_generation.personnages)
    except:
        formatted_data['personnages'] = []
    
    # Ajouter les champs textuels
    formatted_data['illustration'] = game_generation.illustrations_conceptuelles
    formatted_data['pitch_deck'] = game_generation.pitch_deck
    
    return formatted_data

# Vues

@login_required
def home(request):
    user = User.objects.get(id=request.session['user_id'])
    return render(request, 'gameforge/home.html', {'user': user})

@login_required
def generate_game_idea(request):
    user = User.objects.get(id=request.session['user_id'])
    
    if request.method == 'POST':
        # Récupérer les données du formulaire
        title = request.POST.get('title')
        genre = request.POST.get('genre')
        style_graphique = request.POST.get('style_graphique')
        ambiance_visuelle = request.POST.get('ambiance_visuelle')
        ambiance_narrative = request.POST.get('ambiance_narrative')
        mots_cles = request.POST.get('mots_cles')
        reference_culturelle = request.POST.get('reference_culturelle')
        description = request.POST.get('description')

        # Créer une nouvelle idée de jeu
        game_idea = GameIdea.objects.create(
            user=user,
            title=title,
            genre=genre,
            style_graphique=style_graphique,
            ambiance_visuelle=ambiance_visuelle,
            ambiance_narrative=ambiance_narrative,
            mots_cles=mots_cles,
            reference_culturelle=reference_culturelle,
            description=description
        )

        # Rediriger vers la page de l'idée de jeu
        return redirect('game_idea', game_idea_id=game_idea.id)

    return render(request, 'gameforge/generate_game_idea.html', {'user': user})

@login_required
def game_idea(request, game_idea_id):
    game_idea = GameIdea.objects.get(id=game_idea_id)
    user = User.objects.get(id=request.session['user_id'])

    # Vérifier si une génération existe déjà pour cette idée de jeu
    existing_generation = GameGeneration.objects.filter(game_idea=game_idea).first()
    
    if existing_generation:
        # Utiliser la génération existante
        game_generation = existing_generation
    else:
        # Créer une nouvelle génération si aucune n'existe
        generation_data = generate_game_generation(game_idea)
        
        # Créer une nouvelle instance de GameGeneration
        game_generation = GameGeneration.objects.create(
            game_idea=game_idea,
            user=user,
            univers_de_jeu=generation_data['univers'],
            histoire_principale=generation_data['histoire'],
            personnages=generation_data['personnages'],
            illustrations_conceptuelles=generation_data['illustration_url'],
            pitch_deck=generation_data['resume']
        )
    
    # Formater les données pour le template
    formatted_data = format_game_generation_for_template(game_generation)
    
    return render(request, 'gameforge/game_idea.html', {
        'game_idea': game_idea, 
        'game_generation': game_generation,
        'formatted_data': formatted_data
    })

@login_required
def list_game_ideas(request):
    user = User.objects.get(id=request.session['user_id'])
    game_ideas = GameIdea.objects.filter(user=user).order_by('-created_at')
    return render(request, 'gameforge/list_game_ideas.html', {'user': user, 'game_ideas': game_ideas})

@login_required
def search_game_ideas(request):
    query = request.GET.get('q', '')
    user = User.objects.get(id=request.session['user_id'])
    
    if query:
        # Rechercher dans les idées de jeux (exclure les idées de l'utilisateur actuel)
        game_ideas = GameIdea.objects.filter(
            Q(title__icontains=query) | 
            Q(genre__icontains=query) |
            Q(style_graphique__icontains=query) |
            Q(ambiance_visuelle__icontains=query) |
            Q(description__icontains=query)
        ).exclude(user=user).order_by('-created_at')
        
        # Récupérer les générations associées pour l'affichage
        results = []
        for idea in game_ideas:
            generation = GameGeneration.objects.filter(game_idea=idea).first()
            if generation:
                formatted_data = format_game_generation_for_template(generation)
                results.append({
                    'idea': idea,
                    'generation': generation,
                    'formatted_data': formatted_data
                })
    else:
        # Afficher quelques idées récentes pour la découverte
        recent_game_ideas = GameIdea.objects.exclude(user=user).order_by('-created_at')[:6]
        results = []
        for idea in recent_game_ideas:
            generation = GameGeneration.objects.filter(game_idea=idea).first()
            if generation:
                formatted_data = format_game_generation_for_template(generation)
                results.append({
                    'idea': idea,
                    'generation': generation,
                    'formatted_data': formatted_data
                })
    
    return render(request, 'gameforge/search_results.html', {
        'user': user,
        'query': query,
        'results': results,
        'count': len(results)
    })

