from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.urls import reverse
from django.db import models
from django.template.loader import render_to_string
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Game, Move, Challenge
from .forms import JournalForm

import chess


# Create your views here.
@login_required(login_url='login')
def home(request):
    if request.method == 'POST':

        challenged_player_id = request.POST.get('player_black')
        challenged_player = User.objects.get(id=challenged_player_id)

        challenge = Challenge.objects.create(
            challenger=request.user,
            challenged=challenged_player
        )

        # Broadcast the challenge update to the challenged player
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"user_{challenged_player.id}",
            {"type": "broadcast_challenges"}
        )

        messages.success(request, f"Challenge sent to {challenged_player.username}!")
        return redirect('home')
    
    available_players = User.objects.filter(userstatus__is_logged_in=True).exclude(id=request.user.id)
    
    challenges_received = Challenge.objects.filter(challenged=request.user, accepted=None)

    games = Game.objects.filter(
        models.Q(player_white=request.user) | models.Q(player_black=request.user)
    ).order_by('-id')
    
    return render(request, 'engine/home.html', {
        'available_players': available_players,
        'challenges_received': challenges_received,
        'games': games,
    })

@login_required
def heartbeat(request):
    if request.user.is_authenticated:
        request.user.is_logged_in = True
        request.user.save()
        return JsonResponse({'status': 'alive'})
    return JsonResponse({'status': 'error'}, status=400)

def healthcheck(request):
    return JsonResponse({'status': 'alive'})

@login_required(login_url='login')
def delete_game(request, game_id):
    game = get_object_or_404(Game, id=game_id)

    if request.user == game.player_white or request.user == game.player_black:
        game.delete()
        messages.success(request, 'Game has been deleted successfully.')
    else:
        messages.error(request, 'You are not authorized to delete this game.')

    return redirect('home')

@login_required(login_url='login')
def edit_journal(request, game_id):
    game = get_object_or_404(Game, id=game_id)

    if game.player_white != request.user and game.player_black != request.user:
        return HttpResponseForbidden("You are not allowed to edit this journal.")

    if request.method == "POST":
        form = JournalForm(request.POST, instance=game)
        if form.is_valid():
            form.save()
            messages.success(request, "Journal updated successfully!")
            return redirect('home')
    else:
        form = JournalForm(instance=game)

    context = {
        'game': game,
        'form': form,
    }

    return render(request, 'engine/edit_journal.html', context)

def start_new_game(request):
    if request.method == "POST":
        game = Game.objects.create(player_white=request.user, player_black=None)
        return redirect('home')
    
    return render(request, 'engine/start_game.html')

@login_required(login_url='login')
def resign_game(request, game_id):
    game = get_object_or_404(Game, id=game_id)

    if request.user == game.player_white:
        game.winner = game.player_black
    elif request.user == game.player_black:
        game.winner = game.player_white

    game.resignation = True
    game.game_over = True
    game.save()

    channel_layer = get_channel_layer()
    print(f"Player {request.user.username} resigned. Notifying players...")
    async_to_sync(channel_layer.group_send)(
        f"user_{game.player_white.id}",
        {"type": "broadcast_game_history"}
    )
    async_to_sync(channel_layer.group_send)(
        f"user_{game.player_black.id}",
        {"type": "broadcast_game_history"}
    )

    context = {
        'game': game,
        'winner': game.winner,
        'resigned_player': request.user
    }

    async_to_sync(channel_layer.group_send)(
        f"user_{game.player_white.id}",
        {
            "type": "game_resigned",
            "winner": game.winner.username
        }
    )
    print(f"Sent resignation notification to user_{game.player_white.id}")


    async_to_sync(channel_layer.group_send)(
        f"user_{game.player_black.id}",
        {
            "type": "game_resigned",
            "winner": game.winner.username
        }
    )
    print(f"Sent resignation notification to user_{game.player_black.id}")

    return render(request, 'engine/game_over.html', context)

def rules_view(request):
    """
    View to render the rules page.
    """
    return render(request, 'rules.html')

def history_view(request):
    """
    View to render the history page.
    """
    return render(request, 'history.html')

def about_view(request):
    """
    View to render the about page.
    """
    return render(request, 'about.html')

def generate_board_structure_with_labels(board):
    board_structure = []
    for rank in range(8, 0, -1):
        row = []
        for file in range(8):
            square = chess.square(file, rank - 1)
            piece = board.piece_at(square)
            row.append(piece.symbol() if piece else None)
        board_structure.append(row)

    rank_labels = list(range(8, 0, -1))
    zipped_structure = zip(board_structure, rank_labels)
    return zipped_structure

def game_detail(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    board = chess.Board(game.current_fen)

    board_structure = generate_board_structure_with_labels(board)

    if request.method == "POST":
        move_input = request.POST.get("move")

        current_player = game.player_white if board.turn == chess.WHITE else game.player_black

        if request.user != current_player:
            return JsonResponse({'invalid_move': 'It is not your turn!'})

        try:
            move = chess.Move.from_uci(move_input)
        except ValueError:
            return JsonResponse({'invalid_move': 'Invalid move format. Please enter in the correct format (e.g., e2e4).'})

        if move in board.legal_moves:
            board.push(move)
            game.current_fen = board.fen()
            game.save()

            return JsonResponse({'board_fen': board.fen(), 'invalid_move': None, 'turn': board.turn})
        else:
            return JsonResponse({'invalid_move': 'This move is invalid. Please make a legal move.'})

    context = {
        'game': game,
        'board_structure': board_structure,
        'invalid_move': None,
        'is_ongoing': not game.game_over
    }
    return render(request, 'engine/game_detail.html', context)

def update_board(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    board = chess.Board(game.current_fen)

    context = {
        'board_structure': generate_board_structure_with_labels(board),
        'is_ongoing': not game.game_over
    }

    board_html = render_to_string('engine/partials/chessboard.html', context)
    return JsonResponse({'board_html': board_html, 'turn': board.turn})

@csrf_exempt
@login_required(login_url='login')
def respond_challenge(request, challenge_id):
    challenge = get_object_or_404(Challenge, id=challenge_id, challenged=request.user)
    channel_layer = get_channel_layer()

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'accept':
            challenge.accepted = True
            challenge.save()

            game = Game.objects.create(
                player_white=challenge.challenger,
                player_black=challenge.challenged,
                current_fen=chess.Board().fen()
            )

            # Validate that game.id is not None
            if not game.id:
                messages.error(request, "Game creation failed. Please try again.")
                return redirect("home")

            # Notify both players of game start
            async_to_sync(channel_layer.group_send)(
                f"user_{challenge.challenger.id}",
                {
                    "type": "broadcast_game_start",
                    "game_id": game.id
                }
            )
            async_to_sync(channel_layer.group_send)(
                f"user_{challenge.challenged.id}",
                {
                    "type": "broadcast_game_start",
                    "game_id": game.id
                }
            )

            async_to_sync(channel_layer.group_send)(
                f"user_{challenge.challenger.id}",
                {"type": "broadcast_game_history"}
            )
            async_to_sync(channel_layer.group_send)(
                f"user_{challenge.challenged.id}",
                {"type": "broadcast_game_history"}
            )

            return redirect("game_detail", game_id=game.id)
        elif action == 'reject':
            challenge.accepted = False
            challenge.save()

            # Notify the challenger of rejection
            async_to_sync(channel_layer.group_send)(
                f"user_{challenge.challenger.id}",
                {"type": "broadcast_challenges"}
            )

            return redirect("home")
    return redirect("home")

@login_required(login_url='login')
def check_challenges(request):
    challenges_received = Challenge.objects.filter(challenged=request.user, accepted=None)

    challenges_html = render_to_string('engine/partials/challenge_requests.html', {'challenges_received': challenges_received})

    return JsonResponse({'challenges': True, 'challenges_html': challenges_html})

@login_required(login_url='login')
def check_game_start(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'User not authenticated'}, status=403)
    game = Game.objects.filter(
        player_white=request.user,
        game_over=False
    ).first()

    if game:
        return JsonResponse({'game_started': True, 'game_url': reverse('game_detail', args=[game.id])})
    
    return JsonResponse({'game_started': False})

@login_required(login_url='login')
def check_game_status(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    board = chess.Board(game.current_fen)

    if game.game_over:
        return JsonResponse({
            'game_over': True,
            'winner': game.winner.username
        })

    return JsonResponse({
        'game_over': False,
        'board_fen': game.current_fen,
        'turn': board.turn
    })

@login_required(login_url='login')
def game_over(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    
    context = {
        'game': game,
        'winner': game.winner,
    }
    
    return render(request, 'engine/game_over.html', context)