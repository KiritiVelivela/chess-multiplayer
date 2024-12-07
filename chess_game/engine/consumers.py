import json
from channels.generic.websocket import AsyncWebsocketConsumer, AsyncJsonWebsocketConsumer
from django.contrib.auth.models import AnonymousUser, User
from django.urls import reverse
from django.db import models
from asgiref.sync import sync_to_async
from .models import Game, Challenge
from users.models import UserStatus
import chess

class HomeConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        if self.scope["user"].is_authenticated:
            self.user = self.scope["user"]
            # Add the user to a personal group for challenge
            await self.channel_layer.group_add(
                f"user_{self.user.id}",
                self.channel_name
            )
            await self.channel_layer.group_add(
                "home",  # Add user to the general "home" group for available players
                self.channel_name
            )
            await self.accept()
            # Mark user as online
            await sync_to_async(UserStatus.objects.filter(user=self.user).update)(is_logged_in=True)
            await self.send_available_players()  # Notify all users of the updated list
            await self.send_game_history()
        else:
            await self.close()

    async def disconnect(self, close_code):
        if hasattr(self, "user"):
            await self.channel_layer.group_discard(
                f"user_{self.user.id}",
                self.channel_name
            )
            await self.channel_layer.group_discard(
                "home",
                self.channel_name
            )
            # Mark user as offline
            await sync_to_async(UserStatus.objects.filter(user=self.user).update)(is_logged_in=False)
            await self.send_available_players()  # Notify all users of the updated list

    async def receive_json(self, content):
        action = content.get("action")
        if action == "get_challenges":
            await self.send_challenges()
        elif action == "check_game_start":
            await self.check_game_start()
        elif action == "get_available_players":
            await self.send_available_players()
        elif action == "respond_challenge":
            await self.handle_challenge_response(content)
        elif action == "send_challenge":
            await self.handle_send_challenge(content)
        elif action == "edit_journal":
            await self.handle_edit_journal(content)
        elif action == "delete_game":
            await self.handle_delete_game(content)
        elif action == "save_journal":
            await self.save_journal(content)

    async def handle_edit_journal(self, content):
        game_id = content.get("game_id")
        if not game_id:
            await self.send_json({"type": "error", "message": "No game ID provided for editing."})
            return

        try:
            game = await sync_to_async(Game.objects.get)(id=game_id)
            player_white = await sync_to_async(lambda: game.player_white)()
            player_black = await sync_to_async(lambda: game.player_black)()

            if player_white == self.user or player_black == self.user:
                game_data = {
                    "id": game.id,
                    "journal_entry": game.journal_entry or "",
                    "opponent": player_black.username if player_white == self.user else player_white.username,
                }
                await self.send_json({"type": "edit_journal_data", "game": game_data})
            else:
                await self.send_json({"type": "error", "message": "You are not authorized to edit this journal."})
        except Game.DoesNotExist:
            await self.send_json({"type": "error", "message": "Game not found."})

    async def save_journal(self, content):
        game_id = content.get("game_id")
        journal_entry = content.get("journal_entry")

        if not game_id or journal_entry is None:
            await self.send_json({"type": "error", "message": "Invalid data for journal update."})
            return

        try:
            game = await sync_to_async(Game.objects.get)(id=game_id)
            player_white = await sync_to_async(lambda: game.player_white)()
            player_black = await sync_to_async(lambda: game.player_black)()

            if player_white == self.user or player_black == self.user:
                game.journal_entry = journal_entry
                await sync_to_async(game.save)()
                player_white_id = player_white.id if player_white else None
                player_black_id = player_black.id if player_black else None
                if player_white_id:
                    await self.channel_layer.group_send(
                        f"user_{player_white_id}",
                        {
                            "type": "send_game_broadcast",
                            "game_id": game_id,
                        }
                    )
                if player_black_id:
                    await self.channel_layer.group_send(
                        f"user_{player_black_id}",
                        {
                            "type": "send_game_broadcast",
                            "game_id": game_id,
                        }
                    )
            else:
                await self.send_json({"type": "error", "message": "You are not authorized to edit this journal."})
        except Game.DoesNotExist:
            await self.send_json({"type": "error", "message": "Game not found."})

    async def handle_delete_game(self, content):
        game_id = content.get("game_id")
        if not game_id:
            await self.send_json({"type": "error", "message": "No game ID provided for deletion."})
            return

        try:
            game = await sync_to_async(Game.objects.get)(id=game_id)
            player_white = await sync_to_async(lambda: game.player_white)()
            player_black = await sync_to_async(lambda: game.player_black)()
            if player_white == self.user or player_black == self.user:
                # Get the IDs of both players
                player_white_id = player_white.id if player_white else None
                player_black_id = player_black.id if player_black else None

                # Delete the game
                await sync_to_async(game.delete)()
                print(f"Game {game_id} deleted by user {self.user.id}. Broadcasting to involved players.")

                # Notify both players of the deletion
                if player_white_id:
                    await self.channel_layer.group_send(
                        f"user_{player_white_id}",
                        {
                            "type": "delete_game_broadcast",
                            "game_id": game_id,
                        }
                    )
                if player_black_id:
                    await self.channel_layer.group_send(
                        f"user_{player_black_id}",
                        {
                            "type": "delete_game_broadcast",
                            "game_id": game_id,
                        }
                    )
            else:
                await self.send_json({"type": "error", "message": "You are not authorized to delete this game."})
        except Game.DoesNotExist:
            await self.send_json({"type": "error", "message": "Game not found."})

    async def delete_game_broadcast(self, event):
        """
        Broadcast game deletion to the user.
        """
        await self.send_game_history()

    async def handle_send_challenge(self, content):
        """
        Handle sending a challenge to another player.
        """
        player_id = content.get("player_id")
        if not player_id:
            await self.send_json({"type": "error", "message": "No player ID provided for challenge."})
            return

        try:
            challenged_player = await sync_to_async(User.objects.get)(id=player_id)
            # Create challenge
            challenge = await sync_to_async(Challenge.objects.create)(
                challenger=self.user, challenged=challenged_player
            )

            # Notify challenged player
            await self.channel_layer.group_send(
                f"user_{player_id}",
                {"type": "broadcast_challenges"}
            )
            await self.send_json({"type": "success", "message": "Challenge sent successfully!"})
        except User.DoesNotExist:
            await self.send_json({"type": "error", "message": "Player not found."})        

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
        online_users = await sync_to_async(
            lambda: list(UserStatus.objects.filter(is_logged_in=True).values_list('user_id', flat=True))
        )()

        # Broadcast personalized lists to each online user
        for user_id in online_users:
            # Get the available players excluding the current user
            available_players = await sync_to_async(
                lambda: list(
                    UserStatus.objects.filter(is_logged_in=True).exclude(user_id=user_id)
                )
            )()

            players_data = await sync_to_async(
                lambda: [{"id": player.user.id, "username": player.user.username} for player in available_players]
            )()

            # Send personalized list to each user
            await self.channel_layer.group_send(
                f"user_{user_id}",
                {
                    "type": "broadcast_available_players",
                    "players": players_data,
                }
            )

    async def check_game_start(self):
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
        games = await sync_to_async(
            lambda: list(Game.objects.filter(
                models.Q(player_white=self.user) | models.Q(player_black=self.user)
            ).order_by('-id'))
        )()

        games_data = []
        for game in games:
            player_white = await sync_to_async(lambda: game.player_white)()
            player_black = await sync_to_async(lambda: game.player_black)()
            winner = await sync_to_async(lambda: game.winner)()
            games_data.append({
                "id": game.id,
                "opponent": player_black.username if player_white == self.user else player_white.username,
                "result": "Win" if winner == self.user else "Loss" if winner else "Ongoing",
                "move_count": game.move_count,
                "journal_entry": game.journal_entry or "None",
            })

        await self.send_json({
            "type": "game_history",
            "games": games_data,
        })

    async def broadcast_game_history(self, event):
        await self.send_game_history()

    async def broadcast_challenges(self, event):
        await self.send_challenges()

    async def broadcast_game_start(self, event):
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
        await self.send_json({
            "type": "available_players",
            "players": event["players"]
        })

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

        if action == 'move':
            print("INSIDE MOVE RECIEVE")
            await self.handle_move(data.get("move"))
        elif action == 'game_resigned':
            user = self.scope['user']
            await self.handle_resignation(user)
    
    async def game_resigned(self, event):
        winner = event.get("winner")
        print(f"Game resigned event received. Winner: {winner}")
        await self.send_json({
            "status": "game_resigned",
            "winner": winner
        })
    
    async def handle_resignation(self, user):
        try:
            game = await sync_to_async(Game.objects.get)(id=self.game_id)

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
        await self.send_json({
            "type": "game_update",
            "fen": event["fen"],
            "turn": event["turn"],
        })

    async def handle_move(self, move):
        try:
            print("Inside handle_move")
            game = await sync_to_async(Game.objects.get)(id=self.game_id)
            board = chess.Board(game.current_fen)
            player_white = await sync_to_async(lambda: game.player_white)()
            player_black = await sync_to_async(lambda: game.player_black)()

            print(f"player_white = {player_white}")
            print(f"player_black = {player_black}")
            print(f"board.turn = {board.turn}")
            current_player = player_white if board.turn == chess.WHITE else player_black
            print(f"current_player = {current_player}") 
            if self.scope["user"] != current_player:
                print("Not your turn!")
                await self.send_json({"status": "error", "message": "Not your turn!"})
                return

            chess_move = chess.Move.from_uci(move)
            if chess_move in board.legal_moves:
                board.push(chess_move)
                game.current_fen = board.fen()
                await sync_to_async(game.save)()

                await self.channel_layer.group_send(
                    self.game_group_name,
                    {
                        "type": "game_update",
                        "fen": board.fen(),
                        "turn": board.turn == chess.WHITE,
                    }
                )
                print(f"Turn: {board.turn}")
                print(f"Broadcasted update: FEN={board.fen()} Turn={board.turn == chess.WHITE}")
            else:
                print(f"Invalid move: {move}")
                await self.send_json({"status": "error", "message": f"Invalid move: {move} is not allowed!"})
                return
        except Game.DoesNotExist:
            print("GAME NOT FOUND")
            await self.send_json({"status": "error", "message": "Game not found"})