from django.urls import path
from . import views

urlpatterns = [
    path('game/<int:game_id>/resign/', views.resign_game, name='resign_game'),
    path('game/<int:game_id>/status/', views.check_game_status, name='check_game_status'),
    path('game/<int:game_id>/', views.game_detail, name='game_detail'),
    path('game/<int:game_id>/update_board/', views.update_board, name='update_board'),
    path('challenge/<int:challenge_id>/respond/', views.respond_challenge, name='respond_challenge'),
    path('check-challenges/', views.check_challenges, name='check_challenges'),
    path('check-game-start/', views.check_game_start, name='check_game_start'),
    path('game/<int:game_id>/over/', views.game_over, name='game_over'),
    path('game/<int:game_id>/delete/', views.delete_game, name='delete_game'),
    path('game/<int:game_id>/edit_journal/', views.edit_journal, name='edit_journal'),
    path('heartbeat/', views.heartbeat, name='heartbeat'),
    path('healthcheck/', views.healthcheck, name='healthcheck'),
]