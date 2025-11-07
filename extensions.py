from flask_socketio import SocketIO, join_room, leave_room

socketio = SocketIO(cors_allowed_origins="*", async_mode='eventlet')

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