from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import json
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# Game state for score, player positions, bullets, and enemy spawn counter
game_state = {
    'players': {},       # Store player positions
    'scores': {},        # Store player scores individually
    'health': {},        # Store player health
    'bullets': [],       # Track bullets
    'spawn_counter': 0,  # Enemy spawn counter
    'game_over': False
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/game')
def game():
    return render_template('game.html')

@app.route('/quiz')
def quiz():
    return render_template('quiz.html')

@app.route('/get-questions/<type>')
def get_questions(type):
    try:
        if type == 'Debugging':
            with open('static/data/Debugging/5/questions.json') as f:
                questions = json.load(f)
        elif type == 'Git':
            with open('static/data/Git/5/questions.json') as f:
                questions = json.load(f)
        else:
            return jsonify({'error': 'Invalid question type'}), 400
        
        return jsonify(questions)
    except FileNotFoundError:
        return jsonify({'error': 'Questions file not found'}), 404

# Deterministic function for calculating spawn points
def calculate_spawn_point(counter):
    width, height = 800, 600
    x_options = [0, width, width // 2]
    y_options = [0, height, height // 2]

    x = x_options[counter % len(x_options)]
    y = y_options[(counter // len(x_options)) % len(y_options)]
    return {'x': x, 'y': y}

# Emit enemy spawn event at regular intervals
def spawn_enemy():
    game_state['spawn_counter'] += 1
    spawn_point = calculate_spawn_point(game_state['spawn_counter'])
    socketio.emit('enemy_spawned', spawn_point)

@socketio.on('start_enemy_spawn')
def handle_enemy_spawn():
    while not game_state['game_over']:
        spawn_enemy()
        socketio.sleep(1)

@socketio.on('submit_answer')
def handle_answer(data):
    correct = data.get('correct', False)
    points = 20 if correct else -10
    player_id = request.sid
    
    if player_id in game_state['scores']:
        game_state['scores'][player_id] += points
    else:
        game_state['scores'][player_id] = points

    emit('update_score', {'score': game_state['scores'][player_id]}, room=player_id)
    emit('opponent_score', {'score': game_state['scores']}, broadcast=True)

@socketio.on('playerMove')
def handle_player_move(data):
    player_id = request.sid
    position = {'x': data['x'], 'y': data['y']}
    
    game_state['players'][player_id] = position
    emit('update_player_positions', game_state['players'], broadcast=True)

@socketio.on('shootBullet')
def handle_shoot_bullet(data):
    bullet_data = {
        'x': data['x'],
        'y': data['y'],
        'angle': data['angle'],
        'player_id': request.sid
    }
    game_state['bullets'].append(bullet_data)
    emit('bulletFired', bullet_data, broadcast=True)

@socketio.on('healthUpdate')
def handle_health_update(data):
    player_id = data['id']
    health = data['health']
    
    # Update health in game state
    game_state['health'][player_id] = health
    emit('opponent_health', {'id': player_id, 'health': health}, broadcast=True)

@socketio.on('scoreUpdate')
def handle_score_update(data):
    player_id = data['id']
    score = data['score']
    
    game_state['scores'][player_id] = score
    emit('opponent_score', {'id': player_id, 'score': score}, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    player_id = request.sid
    if player_id in game_state['players']:
        del game_state['players'][player_id]
    if player_id in game_state['scores']:
        del game_state['scores'][player_id]
    if player_id in game_state['health']:
        del game_state['health'][player_id]
    
    emit('removePlayer', player_id, broadcast=True)

if __name__ == '__main__':
    socketio.start_background_task(handle_enemy_spawn)
    socketio.run(app, host='0.0.0.0', port=8000)
