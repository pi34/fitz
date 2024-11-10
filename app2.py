from flask import Flask, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import random

app = Flask(__name__)
socketio = SocketIO(app)

players = {}

def handle_new_player(player_id, x=0, y=0, health=100):
    """Handles a new player joining the game."""
    players[player_id] = {
        'id': player_id,
        'x': x,
        'y': y,
        'health': health
    }
    emit('newPlayer', players[player_id], broadcast=True)
    emit('currentPlayers', players)

def handle_player_move(player_id, x, y):
    """Updates a player's position and broadcasts it."""
    if player_id in players:
        players[player_id]['x'] = x
        players[player_id]['y'] = y
        emit('playerMoved', players[player_id], broadcast=True, include_self=False)

@socketio.on('playerMove')
def on_player_move(data):
    """Receive movement data from client and update player position."""
    player_id = request.sid
    x = data.get('x')
    y = data.get('y')
    handle_player_move(player_id, x, y)

@socketio.on('newPlayer')
def on_new_player(data):
    """Initialize new player with starting position and health."""
    player_id = request.sid
    x = random.randint(50, 750)  # Example spawn location
    y = random.randint(50, 550)
    handle_new_player(player_id, x, y)

@socketio.on('disconnect')
def on_disconnect():
    """Handle player disconnection."""
    player_id = request.sid
    if player_id in players:
        del players[player_id]
        emit('playerDisconnected', player_id, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, debug=True)
