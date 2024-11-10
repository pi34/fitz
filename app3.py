from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app)

# Dictionary to keep track of players and their states
players = {}

@app.route('/')
def index():
    return render_template('index.html')  # Assumes an `index.html` file as the main client page

@socketio.on('connect')
def handle_connect():
    player_id = request.sid  # Unique player session ID
    # Initialize player state
    players[player_id] = {'x': 400, 'y': 300, 'health': 100}
    
    # Notify the connecting player of all current players
    emit('currentPlayers', players, to=player_id)
    # Notify all other players about the new player
    emit('newPlayer', {'id': player_id, **players[player_id]}, broadcast=True, include_self=False)
    print(f'Player connected: {player_id}')

@socketio.on('disconnect')
def handle_disconnect():
    player_id = request.sid
    if player_id in players:
        del players[player_id]
        # Inform all clients that a player has disconnected
        emit('playerDisconnected', player_id, broadcast=True)
    print(f'Player disconnected: {player_id}')

@socketio.on('playerMove')
def handle_player_move(data):
    player_id = request.sid
    if player_id in players:
        # Update player coordinates
        players[player_id]['x'] += data['x']
        players[player_id]['y'] += data['y']
        # Broadcast the updated position to other players
        emit('playerMoved', {'id': player_id, **players[player_id]}, broadcast=True, include_self=False)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=3000)
