import json
from channels.generic.websocket import AsyncWebsocketConsumer, AsyncJsonWebsocketConsumer
from django.contrib.auth.models import AnonymousUser, User
from django.urls import reverse
from django.db import models
from asgiref.sync import sync_to_async
from .models import Game, Challenge
from users.models import UserStatus
import chess

# engine/consumers.py
# from channels.generic.websocket import AsyncJsonWebsocketConsumer
# from django.contrib.auth.models import User
# from .models import Challenge, Game

class HomeConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        """
        Handle WebSocket connection. Add the user to a personal group if authenticated.
        """
        if self.scope["user"].is_authenticated:
            self.user = self.scope["user"]
            # Add the user to a personal group for challenge and game updates
            await self.channel_layer.group_add(
                f"user_{self.user.id}",
                self.channel_name
            )
            await self.channel_layer.group_add(
                "home",  # Add user to the general "home" group for available players
                self.channel_name
            )
            await self.accept()
        else:
            await self.close()

    async def disconnect(self, close_code):
        """
        Handle WebSocket disconnection. Remove the user from the groups.
        """
        if hasattr(self, "user"):
            await self.channel_layer.group_discard(
                f"user_{self.user.id}",
                self.channel_name
            )
            await self.channel_layer.group_discard(
                "home",
                self.channel_name
            )

    async def receive_json(self, content):
        """
        Handle messages from the client. Perform actions based on the "action" key.
        """
        action = content.get("action")
        if action == "get_challenges":
            await self.send_challenges()
        elif action == "check_game_start":
            await self.check_game_start()
        elif action == "get_available_players":
            await self.send_available_players()
        elif action == "respond_challenge":
            await self.handle_challenge_response(content)

    async def send_challenges(self):
        """
        Send the list of challenges to the user.
        """
        challenges = await sync_to_async(
            lambda: Challenge.objects.filter(challenged=self.user, accepted=None)
        )()
        challenges_data = await sync_to_async(
            lambda: [{"id": ch.id, "challenger": ch.challenger.username} for ch in challenges]
        )()
        await self.send_json({
            "type": "challenges",
            "challenges": challenges_data
        })

    
    async def handle_challenge_response(self, content):
        """
        Handle challenge responses (accept/reject).
        """
        challenge_id = content.get("challenge_id")
        response = content.get("response")
        if not challenge_id or not response:
            await self.send_json({
                "type": "error",
                "message": "Invalid challenge response data."
            })
            return

        challenge = await sync_to_async(Challenge.objects.get)(id=challenge_id)
        challenger = await sync_to_async(lambda: challenge.challenger)()
        challenged = await sync_to_async(lambda: challenge.challenged)()
        if challenged != self.user:
            await self.send_json({
                "type": "error",
                "message": "You are not authorized to respond to this challenge."
            })
            return

        if response == "accept":
            challenge.accepted = True
            await sync_to_async(challenge.save)()

            # Create a new game
            game = await sync_to_async(Game.objects.create)(
                player_white=challenger,
                player_black=challenged,
                current_fen=chess.Board().fen()
            )

            # Notify both players of game start
            await self.channel_layer.group_send(
                f"user_{challenger.id}",
                {
                    "type": "broadcast_game_start",
                    "game_id": game.id
                }
            )
            await self.channel_layer.group_send(
                f"user_{challenged.id}",
                {
                    "type": "broadcast_game_start",
                    "game_id": game.id
                }
            )
        elif response == "reject":
            challenge.accepted = False
            await sync_to_async(challenge.save)()

            # Notify challenger of rejection
            await self.channel_layer.group_send(
                f"user_{challenger.id}",
                {
                    "type": "broadcast_challenges",
                }
            )

        # Send updated challenges to the challenged player
        await self.send_challenges()

    async def send_available_players(self):
        """
        Send the list of currently online players, excluding the current user.
        """
        players = await sync_to_async(
            lambda: UserStatus.objects.filter(is_logged_in=True).exclude(user=self.user)
        )()
        players_data = await sync_to_async(
            lambda: [{"id": player.user.id, "username": player.user.username} for player in players]
        )()
        await self.send_json({
            "type": "available_players",
            "players": players_data
        })

    async def check_game_start(self):
        """
        Check if the user has an active game and notify the client.
        """
        game = await sync_to_async(
            lambda: Game.objects.filter(
                models.Q(player_white=self.user) | models.Q(player_black=self.user),
                game_over=False
            ).first()
        )()
        if game:
            await self.send_json({
                "type": "game_start",
                "url": reverse("game_detail", args=[game.id])
            })

    async def send_game_history(self):
        """
        Send the updated game history to the user.
        """
        games = await sync_to_async(
            lambda: Game.objects.filter(
                models.Q(player_white=self.user) | models.Q(player_black=self.user)
            ).order_by('-id')
        )()
        games_data = await sync_to_async(
            lambda: [
                {
                    "id": game.id,
                    "opponent": game.player_black.username if game.player_white == self.user else game.player_white.username,
                    "result": "Win" if game.winner == self.user else "Loss" if game.winner else "Ongoing",
                    "move_count": game.move_count,
                    "journal_entry": game.journal_entry or "None",
                }
                for game in games
            ]
        )()
        await self.send_json({
            "type": "game_history",
            "games": games_data,
        })

    async def broadcast_game_history(self, event):
        """
        Broadcast updated game history data to the user when changes occur.
        """
        await self.send_game_history()

    async def broadcast_challenges(self, event):
        """
        Broadcast updated challenge data to the user when changes occur.
        """
        await self.send_challenges()

    async def broadcast_game_start(self, event):
        """
        Broadcast game start information to the user.
        """
        game_id = event.get("game_id")
        
        if not game_id:
            # Log or gracefully handle missing game_id
            await self.send_json({
                "type": "error",
                "message": "Game ID is missing. Cannot start the game."
            })
            return

        # Generate the game URL
        game_url = reverse("game_detail", args=[game_id])
        await self.send_json({
            "type": "game_start",
            "game_url": game_url,
        })

    async def broadcast_available_players(self, event):
        """
        Broadcast the updated list of available players to the client.
        """
        await self.send_available_players()

class GameConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.game_id = self.scope['url_route']['kwargs']['game_id']
        self.game_group_name = f'game_{self.game_id}'

        # Add the user to the group
        await self.channel_layer.group_add(
            self.game_group_name,
            self.channel_name
        )
        print(f"Added user to game group: {self.game_group_name}")

        await self.accept()

    async def disconnect(self, close_code):
        # Remove the user from the group
        await self.channel_layer.group_discard(
            self.game_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')

        # Example: Handle move submission
        if action == 'move':
            move = data['move']
            user = self.scope['user']
            response = await self.handle_move(user, move)

            # Send updated board state to the group
            await self.channel_layer.group_send(
                self.game_group_name,
                {
                    'type': 'game_update',
                    'message': response
                }
            )
        elif action == 'game_resigned':
            user = self.scope['user']
            await self.handle_resignation(user)
    
    async def game_resigned(self, event):
        """
        Notify players that the game has been resigned and redirect them.
        """
        winner = event.get("winner")
        print(f"Game resigned event received. Winner: {winner}")
        await self.send_json({
            "type": "game_resigned",
            "winner": winner
        })
    
    async def handle_resignation(self, user):
        """
        Handle the resignation logic and notify all players in the game.
        """
        try:
            game = await sync_to_async(Game.objects.get)(id=self.game_id)

            # Fetch foreign key fields asynchronously
            player_white = await sync_to_async(lambda: game.player_white)()
            player_black = await sync_to_async(lambda: game.player_black)()

            if user == player_white:
                game.winner = player_black
            elif user == player_black:
                game.winner = player_white
            else:
                return

            game.resignation = True
            game.game_over = True
            await sync_to_async(game.save)()

            # Broadcast the resignation to all players in the group
            await self.channel_layer.group_send(
                self.game_group_name,
                {
                    'type': 'game_resigned',
                    'winner': game.winner.username
                }
            )

        except Game.DoesNotExist:
            print("Game not found.")

    async def game_update(self, event):
        # Send the updated board state to the WebSocket
        await self.send(text_data=json.dumps(event['message']))

    @sync_to_async
    def handle_move(self, user, move):
        # Process move logic here
        try:
            game = Game.objects.get(id=self.game_id)
            board = chess.Board(game.current_fen)

            if user == game.player_white if board.turn else game.player_black:
                chess_move = chess.Move.from_uci(move)
                if chess_move in board.legal_moves:
                    board.push(chess_move)
                    game.current_fen = board.fen()
                    game.save()

                    return {'status': 'success', 'fen': board.fen(), 'turn': board.turn}
                else:
                    return {'status': 'error', 'message': 'Invalid move'}
            else:
                return {'status': 'error', 'message': 'Not your turn'}
        except Game.DoesNotExist:
            return {'status': 'error', 'message': 'Game not found'}