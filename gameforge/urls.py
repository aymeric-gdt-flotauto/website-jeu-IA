from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("generate/", views.generate_game_idea, name="generate_game_idea"),
    path("idea/<int:game_idea_id>/", views.game_idea, name="game_idea"),
    path("ideas/", views.list_game_ideas, name="list_game_ideas"),
    path("search/", views.search_game_ideas, name="search_game_ideas"),
] 