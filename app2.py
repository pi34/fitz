from flask import Flask, render_template, request, jsonify, redirect, url_for, json
from flask_socketio import SocketIO, emit, join_room, leave_room
import google.generativeai as genai
from dotenv import load_dotenv
import random
import string
import json
import os
from datetime import datetime

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
socketio = SocketIO(app)

# Configure Gemini
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
model = genai.GenerativeModel('gemini-pro')

# Storage
quizzes = {}   # {quiz_id: {topic, questions, scores: [{player1, player2, score, date}]}}
game_rooms = {} # {room_code: GameRoom()}

class GameRoom:
    def __init__(self, quiz_id):
        self.quiz_player = None
        self.game_player = None
        self.quiz_id = quiz_id
        self.quiz_state = {
            'current_questions': [],
            'current_index': 0,
            'score': 0
        }
        self.game_state = {
            'score': 0
        }
        self.start_time = datetime.now()
        self.last_activity = datetime.now()

    def update_activity(self):
        """Update the last activity timestamp"""
        self.last_activity = datetime.now()

    def get_completion_status(self, total_questions):
        """Get the completion status of this game room"""
        if self.quiz_state['current_index'] >= total_questions:
            return 'Completed'
        return 'Active'

# Main routes
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/student/quiz/<quiz_id>')
def quiz_lobby(quiz_id):
    if quiz_id not in quizzes:
        return redirect(url_for('student_dashboard'))
    return render_template('student/quiz_lobby.html', quiz_id=quiz_id, quiz=quizzes[quiz_id])

@app.route('/teacher')
def teacher_dashboard():
    return render_template(
        'teacher/dashboard.html',
        quizzes=quizzes,
        game_rooms=game_rooms,
        request=request  # Pass request object for generating URLs
    )

@app.route('/teacher/quiz-scores/<quiz_id>')
def quiz_scores(quiz_id):
    if quiz_id not in quizzes:
        return jsonify({'error': 'Quiz not found'}), 404
    
    # Get all game rooms for this quiz
    quiz_game_rooms = []
    for room_code, room in game_rooms.items():
        if room.quiz_id == quiz_id:
            quiz_game_rooms.append({
                'room_code': room_code,
                'quiz_state': room.quiz_state,
                'total_questions': len(quizzes[quiz_id]['questions']),
                'start_time': room.start_time.isoformat() if hasattr(room, 'start_time') else None,
                'last_activity': room.last_activity.isoformat() if hasattr(room, 'last_activity') else None
            })
    
    return jsonify({
        'topic': quizzes[quiz_id]['topic'],
        'game_rooms': quiz_game_rooms
    })

@app.route('/create_game_room', methods=['POST'])
def create_game_room():
    data = request.get_json()
    quiz_id = data.get('quiz_id')
    
    if quiz_id not in quizzes:
        return jsonify({'error': 'Invalid quiz ID'}), 404
    
    room_code = generate_room_code()
    game_rooms[room_code] = GameRoom(quiz_id)
    
    # Set up the game room with quiz questions
    game_rooms[room_code].quiz_state['current_questions'] = quizzes[quiz_id]['questions']
    
    return jsonify({'room_code': room_code})

@app.route('/quiz/<room>')
def quiz_game(room):
    if room not in game_rooms:
        return redirect(url_for('student_dashboard'))
    
    quiz_id = game_rooms[room].quiz_id
    quiz = quizzes[quiz_id]
    
    # Optionally shuffle questions
    import random
    shuffled_questions = quiz['questions'].copy()
    random.shuffle(shuffled_questions)
    
    # Create a safe JSON string for the template
    questions_json = json.dumps(shuffled_questions)
    
    return render_template('quiz.html', 
                         room=room, 
                         quiz={'topic': quiz['topic']},
                         questions_json=questions_json) 

@app.route('/game/<room>')
def game(room):
    if room not in game_rooms:
        return redirect(url_for('student_dashboard'))
    return render_template('game.html', room=room)

@app.route('/teacher/quiz-scores/<quiz_id>')
def get_quiz_scores(quiz_id):
    try:
        if quiz_id not in quizzes:
            return jsonify({'error': 'Quiz not found'}), 404
        
        quiz = quizzes[quiz_id]
        total_questions = len(quiz['questions'])
        
        # Get all game rooms for this quiz
        quiz_game_rooms = []
        for room_code, room in game_rooms.items():
            if room.quiz_id == quiz_id:
                room_data = {
                    'room_code': room_code,
                    'quiz_state': {
                        'current_index': room.quiz_state['current_index'],
                        'score': room.quiz_state['score']
                    },
                    'start_time': room.start_time.isoformat() if hasattr(room, 'start_time') else None,
                    'last_activity': room.last_activity.isoformat() if hasattr(room, 'last_activity') else None,
                    'total_questions': total_questions,
                    'status': 'Completed' if room.quiz_state['current_index'] >= total_questions else 'Active'
                }
                quiz_game_rooms.append(room_data)
        
        return jsonify({
            'quiz_topic': quiz['topic'],  # Changed from nested structure
            'game_rooms': quiz_game_rooms,
            'total_questions': total_questions
        })
        
    except Exception as e:
        print(f"Error getting quiz scores: {str(e)}")
        return jsonify({'error': 'Failed to load scores'}), 500


def clean_json_response(text):
    """Clean up the Gemini response to ensure valid JSON"""
    # Remove code blocks
    text = text.replace('```json', '').replace('```', '').strip()
    
    # Replace quotes
    text = text.replace("'", '"')
    text = text.replace(""", '"').replace(""", '"')
    text = text.replace("'", '"').replace("'", '"')
    
    # Fix common JSON issues
    text = text.replace('}, {', "},\n{")  # Add newlines between objects
    text = text.replace('},]', '}]')  # Fix trailing comma
    text = text.replace(',]', ']')  # Fix trailing comma
    
    # Ensure array brackets
    if not text.startswith('['):
        text = '[' + text
    if not text.endswith(']'):
        text = text + ']'
    
    return text

def validate_question(question):
    """Validate a single question object"""
    if not isinstance(question, dict):
        return False
        
    required_fields = ['question', 'options', 'correct_answer', 'explanation']
    if not all(field in question for field in required_fields):
        return False
        
    if not isinstance(question['options'], list) or len(question['options']) != 4:
        return False
        
    if question['correct_answer'] not in question['options']:
        return False
        
    return True


@app.route('/teacher/create_quiz', methods=['POST'])
def create_quiz():
    try:
        data = request.get_json()
        topic = data.get('topic')
        num_questions = data.get('num_questions', 5)
        
        # More specific prompt to ensure valid JSON format
        prompt = f"""Create {num_questions} multiple choice questions about {topic}. 
        Format each question as shown in this example:
        [
            {{
                "question": "What is the capital of France?",
                "options": ["London", "Paris", "Berlin", "Madrid"],
                "correct_answer": "Paris",
                "explanation": "Paris is the capital city of France."
            }}
        ]

        Rules:
        1. Create exactly {num_questions} questions
        2. Use the EXACT format shown above
        3. Each question must have exactly 4 options
        4. Make sure the correct_answer matches one of the options exactly
        5. Use only straight double quotes (")
        6. Include proper JSON commas and brackets
        7. Make sure it's valid JSON format

        Respond with the questions array only, no other text."""

        # Generate content
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Clean up the response
        response_text = response_text.replace('```json', '').replace('```', '').strip()
        print("Raw response:", response_text)  # Debug print
        
        try:
            # Try to parse JSON
            questions = json.loads(response_text)
            
            # Validate format
            if not isinstance(questions, list):
                raise ValueError("Response is not a list of questions")
            
            validated_questions = []
            for q in questions:
                if not isinstance(q, dict):
                    continue
                    
                # Check required fields
                required_fields = ['question', 'options', 'correct_answer', 'explanation']
                if not all(field in q for field in required_fields):
                    continue
                    
                # Validate options
                if not isinstance(q['options'], list) or len(q['options']) != 4:
                    continue
                    
                # Validate correct answer
                if q['correct_answer'] not in q['options']:
                    continue
                    
                validated_questions.append(q)
            
            if not validated_questions:
                return jsonify({'error': 'No valid questions generated'}), 500
            
            # Create quiz
            quiz_id = str(len(quizzes) + 1).zfill(3)  # e.g., "001", "002"
            quizzes[quiz_id] = {
                'topic': topic,
                'questions': validated_questions,
                'game_rooms': []
            }
            
            return jsonify({
                'quiz_id': quiz_id,
                'topic': topic,
                'num_questions': len(validated_questions)
            })
            
        except json.JSONDecodeError as e:
            # If JSON parsing fails, try to clean up the response
            print("JSON Parse Error:", str(e))
            
            # Try to fix common JSON issues
            cleaned_text = response_text
            cleaned_text = cleaned_text.replace("'", '"')  # Replace single quotes
            cleaned_text = cleaned_text.replace(""", '"').replace(""", '"')  # Replace smart quotes
            
            # Ensure it's wrapped in array brackets
            if not cleaned_text.startswith('['):
                cleaned_text = '[' + cleaned_text
            if not cleaned_text.endswith(']'):
                cleaned_text = cleaned_text + ']'
            
            try:
                questions = json.loads(cleaned_text)
                # ... (same validation as above)
                
            except json.JSONDecodeError:
                return jsonify({'error': 'Invalid question format generated'}), 500
            
    except Exception as e:
        print("Error generating quiz:", str(e))
        return jsonify({'error': 'Failed to generate quiz'}), 500

@app.route('/teacher/scores')
def view_scores():
    return render_template('teacher/scores.html', quizzes=quizzes)

# Student routes
@app.route('/student')
def student_dashboard():
    return render_template('student/dashboard.html', quizzes=quizzes)


# Helper functions
def generate_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def generate_room_code():
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if code not in game_rooms:
            return code

# Socket events
@socketio.on('join')
def on_join(data):
    room = data.get('room')
    player_type = data.get('player_type')
    
    if not room or room not in game_rooms:
        emit('error', {'message': 'Invalid room'})
        return

    join_room(room)
    
    if player_type == 'quiz':
        game_rooms[room].quiz_player = request.sid
    else:
        game_rooms[room].game_player = request.sid
    
    # Emit current room status
    emit('player_joined', {
        'player_type': player_type,
        'room_status': {
            'quiz_player': game_rooms[room].quiz_player is not None,
            'game_player': game_rooms[room].game_player is not None
        }
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

@socketio.on('submit_answer')
def handle_answer(data):
    room = data.get('room')
    if not room or room not in game_rooms:
        return
    
    game_rooms[room].last_activity = datetime.now()  # Update last activity
    
    correct = data.get('correct', False)
    points = 20 if correct else -10
    
    game_rooms[room].quiz_state['score'] += points
    
    emit('update_score', {
        'score': points,
        'correct': correct
    }, to=room)

if __name__ == '__main__':
    socketio.run(app, port=8000, host='0.0.0.0', debug=True)