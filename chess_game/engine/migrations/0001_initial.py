# Generated by Django 4.2.16 on 2024-10-18 22:56

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Game',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('current_fen', models.CharField(default='rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1', max_length=100)),
                ('game_over', models.BooleanField(default=False)),
                ('winner', models.CharField(blank=True, max_length=5, null=True)),
                ('player_black', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='black_player', to=settings.AUTH_USER_MODEL)),
                ('player_white', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='white_player', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Move',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uci_move', models.CharField(max_length=10)),
                ('move_number', models.IntegerField()),
                ('game', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='moves', to='engine.game')),
            ],
        ),
    ]
