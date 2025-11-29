from flask_socketio import SocketIO, join_room, leave_room
from flask_restx import Api
from flask_wtf.csrf import CSRFProtect

# Initialize extensions
socketio = SocketIO(cors_allowed_origins="*", async_handlers=True)
api = Api(
    version='1.0', 
    title='MediQueue API', 
    description='API for MediQueue application',
    doc='/api/docs',
    prefix='/api'
)
csrf = CSRFProtect()

@socketio.on('join')
def handle_join(data):
    room = data.get('room') 
    if room:
        join_room(room)

@socketio.on('leave')
def handle_leave(data):
    room = data.get('room')
    if room:
        leave_room(room)