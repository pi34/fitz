from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# Game state for score
game_state = {'score': 0}

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
            with open('static/assets/data/Git/5/questions.json') as f:
                questions = json.load(f)
        else:
            return jsonify({'error': 'Invalid question type'}), 400
        
        return jsonify(questions)
    except FileNotFoundError:
        return jsonify({'error': 'Questions file not found'}), 404

# Handle quiz answer submissions
@socketio.on('submit_answer')
def handle_answer(data):
    correct = data.get('correct', False)
    # Adjust score based on quiz answer
    points = 0
    if correct:
        points += 20  # Increase score for correct answer
    else:
        points -= 10   # Decrease score for incorrect answer

    # Broadcast the updated score to all clients on the game page
    emit('update_score', {'score': points}, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, port=8000, host='172.20.10.2', debug=True)