from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from flask_socketio import SocketIO, emit, join_room, leave_room
import google.generativeai as genai
from dotenv import load_dotenv
import json
import random
import string
import os

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# Configure Gemini API
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
model = genai.GenerativeModel('gemini-pro')

# Store active game rooms
game_rooms = {}

def generate_room_code():
    """Generate a unique 6-character room code"""
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if code not in game_rooms:
            return code

game_rooms = {}

class GameRoom:
    def __init__(self):
        self.quiz_player = None
        self.game_player = None
        self.quiz_state = {
            'current_questions': [],
            'current_index': 0,
            'score': 0
        }
        self.game_state = {
            'score': 0
        }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create-room', methods=['POST'])
def create_room():
    room_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    game_rooms[room_code] = GameRoom()
    return jsonify({'room_code': room_code})

@app.route('/join-room', methods=['POST'])
def join_room_route():
    data = request.get_json()
    room_code = data.get('room_code', '').upper()
    player_type = data.get('player_type')
    
    if room_code not in game_rooms:
        return jsonify({'error': 'Invalid room code'}), 404
    
    room = game_rooms[room_code]
    
    # Check if the requested player type slot is available
    if player_type == 'quiz' and room.quiz_player is not None:
        return jsonify({'error': 'Quiz player slot is already taken'}), 400
    elif player_type == 'game' and room.game_player is not None:
        return jsonify({'error': 'Game player slot is already taken'}), 400
    
    # Assign player to room
    if player_type == 'quiz':
        room.quiz_player = True
        return jsonify({'redirect': f'/quiz/{room_code}'})
    else:
        room.game_player = True
        return jsonify({'redirect': f'/game/{room_code}'})


@app.route('/quiz/<room>')
def quiz(room):
    if room not in game_rooms:
        return redirect(url_for('index'))
    return render_template('quiz.html', room=room)

@app.route('/game/<room>')
def game(room):
    if room not in game_rooms:
        return redirect(url_for('index'))
    return render_template('game.html', room=room)

@socketio.on('join')
def on_join(data):
    room = data.get('room')
    player_type = data.get('player_type')
    
    if not room or room not in game_rooms:
        emit('error', {'message': 'Invalid room'})
        return

    join_room(room)
    
    # Update room status
    if player_type == 'quiz':
        game_rooms[room].quiz_player = request.sid
    else:
        game_rooms[room].game_player = request.sid
    
    # Emit current room status to all players in the room
    room_status = {
        'quiz_player': game_rooms[room].quiz_player is not None,
        'game_player': game_rooms[room].game_player is not None
    }
    
    print(f"Room {room} status: {room_status}")  # Debug print
    
    emit('player_joined', {
        'player_type': player_type,
        'room_status': room_status
    }, to=room)

@socketio.on('disconnect')
def on_disconnect():
    for room_code, room in game_rooms.items():
        if room.quiz_player == request.sid:
            room.quiz_player = None
            emit('player_left', {
                'player_type': 'quiz',
                'room_status': {
                    'quiz_player': False,
                    'game_player': room.game_player is not None
                }
            }, to=room_code)
            break
        elif room.game_player == request.sid:
            room.game_player = None
            emit('player_left', {
                'player_type': 'game',
                'room_status': {
                    'quiz_player': room.quiz_player is not None,
                    'game_player': False
                }
            }, to=room_code)
            break

def generate_questions(topic):
    """Generate quiz questions using Gemini"""
    try:
        prompt = f"""Generate 5 multiple choice questions about {topic}. 
        Format the response as a JSON array of question objects. Each question should have this exact structure:
        {{
            "question": "question text",
            "options": ["option1", "option2", "option3", "option4"],
            "correct_answer": "correct option",
            "explanation": "explanation of the correct answer"
        }}
        
        Make sure:
        1. The response is valid JSON that can be parsed
        2. Each question has exactly 4 options
        3. The correct_answer matches exactly one of the options
        4. Include clear explanations
        
        Return only the JSON array without any additional text."""

        response = model.generate_content(prompt)
        
        # Extract JSON from response
        response_text = response.text.strip()
        # Remove any markdown code block indicators if present
        response_text = response_text.replace('```json', '').replace('```', '').strip()
        
        # Parse the response into JSON
        questions = json.loads(response_text)
        
        # Validate question format
        for question in questions:
            if not all(key in question for key in ['question', 'options', 'correct_answer', 'explanation']):
                raise ValueError("Invalid question format")
            if len(question['options']) != 4:
                raise ValueError("Each question must have exactly 4 options")
            if question['correct_answer'] not in question['options']:
                raise ValueError("Correct answer must be one of the options")
        
        return questions
    except Exception as e:
        print(f"Error generating questions: {str(e)}")
        return []

# Modified quiz-related routes to include room functionality
@app.route('/generate-quiz', methods=['POST'])
def generate_quiz():
    try:
        data = request.get_json()
        room = data.get('room')
        topic = data.get('topic', 'general knowledge')
        num_questions = data.get('num_questions', 5)  # Default to 5 questions
        
        if not room or room not in game_rooms:
            return jsonify({'error': 'Invalid room'}), 404

        # Generate multiple questions at once
        prompt = f"""Generate {num_questions} multiple choice questions about {topic}.
        Format your response as a JSON array of question objects, where each question has this structure:
        {{
            "question": "What is the question text here?",
            "options": ["first option", "second option", "third option", "fourth option"],
            "correct_answer": "second option",
            "explanation": "Explanation why second option is correct"
        }}

        Rules:
        1. Generate exactly {num_questions} questions
        2. Each question must be properly formatted JSON
        3. Use double quotes for strings
        4. Each correct_answer must exactly match one of the options
        5. Questions should be about {topic}
        6. Each question should have exactly 4 options
        
        Return ONLY the JSON array of questions, nothing else."""

        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Clean up and parse response
        response_text = response_text.replace('```json', '').replace('```', '').strip()
        questions = json.loads(response_text)
        
        # Validate questions
        validated_questions = []
        for question in questions:
            if (all(key in question for key in ['question', 'options', 'correct_answer', 'explanation']) and
                len(question['options']) == 4 and
                question['correct_answer'] in question['options']):
                validated_questions.append(question)
        
        if not validated_questions:
            return jsonify({'error': 'Failed to generate valid questions'}), 500

        # Store questions in room state
        game_rooms[room].quiz_state['current_questions'] = validated_questions
        game_rooms[room].quiz_state['current_index'] = 0
        
        # Return first question and total count
        return jsonify({
            'total_questions': len(validated_questions),
            'current_question': validated_questions[0]
        })
            
    except Exception as e:
        print(f"Error generating questions: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/next-question', methods=['GET'])
def next_question():
    try:
        room = request.args.get('room')
        if not room or room not in game_rooms:
            return jsonify({'error': 'Invalid room'}), 404
        
        room_state = game_rooms[room].quiz_state
        current_questions = room_state['current_questions']
        current_index = room_state['current_index']
        
        # Move to next question
        current_index += 1
        room_state['current_index'] = current_index
        
        # Check if quiz is finished
        if current_index >= len(current_questions):
            return jsonify({
                'finished': True,
                'total_score': room_state['score']
            })
        
        # Return next question
        return jsonify({
            'question': current_questions[current_index],
            'question_number': current_index + 1,
            'total_questions': len(current_questions)
        })
        
    except Exception as e:
        print(f"Error getting next question: {str(e)}")
        return jsonify({'error': str(e)}), 500

@socketio.on('submit_answer')
def handle_answer(data):
    room = data.get('room')
    if not room or room not in game_rooms:
        emit('error', {'message': 'Invalid room'})
        return
    
    correct = data.get('correct', False)
    points = 20 if correct else -10
    
    # Debug print
    print(f"Answer submitted in room {room}: {'Correct' if correct else 'Incorrect'}")
    
    # Emit score update to the game room
    emit('update_score', {
        'score': points,
        'correct': correct
    }, to=room)

# Add game mechanics events
@socketio.on('game_event')
def handle_game_event(data):
    room = session.get('room')
    if not room or room not in game_rooms:
        return
    
    # Forward game events to all players in the room
    emit('game_update', data, room=room)

if __name__ == '__main__':
    socketio.run(app, port=8000, host='0.0.0.0', debug=True)