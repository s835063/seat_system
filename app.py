from flask import Flask, render_template, request, redirect, url_for, session, send_file
from flask_socketio import SocketIO, emit
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import eventlet
import io
from utils.qrcode_generator import generate_qrcode

eventlet.monkey_patch()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey'

socketio = SocketIO(app, cors_allowed_origins="*")

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# 產生 50 組學生帳號及密碼
users = {
    **{f'student{str(i).zfill(2)}': 
        {'password': f'pass{str(i).zfill(3)}', 'name': f'學生{str(i).zfill(2)}', 'role': 'student'}
        for i in range(1, 51)
    },
    # 管理員帳號
         'admin01': {'password': 'admin123', 'name': '管理員', 'role': 'admin'}}

class User(UserMixin):
    def __init__(self, id):
        self.id = id
        self.name = users[id]['name']
        self.role = users[id]['role']

@login_manager.user_loader
def load_user(user_id):
    if user_id in users:
        return User(user_id)
    return None

seats = {i: True for i in range(1, 41)}
user_selections = {}

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        uid = request.form.get('username')
        pwd = request.form.get('password')
        if uid in users and users[uid]['password'] == pwd:
            user = User(uid)
            login_user(user)
            return redirect(url_for('seat_select'))
        return render_template('login.html', error="帳號或密碼錯誤")
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    user_id = current_user.id
    if user_id in user_selections:
        seat_num = user_selections.pop(user_id)
        seats[seat_num] = True
        socketio.emit('seat_update', {'seat_num': seat_num, 'status': True}, broadcast=True)
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def seat_select():
    return render_template('seat_select.html', name=current_user.name)

@app.route('/admin')
@login_required
def admin():
    if current_user.role != 'admin':
        return "無權限", 403
    return render_template('admin.html', seats=seats)

@socketio.on('connect')
@login_required
def on_connect():
    emit('seat_status', seats)

@socketio.on('select_seat')
@login_required
def on_select_seat(data):
    user_id = current_user.id
    seat_num = data.get('seat_num')
    if seat_num is None or not isinstance(seat_num, int) or seat_num not in seats:
        emit('error', {'msg': '座位編號錯誤'})
        return
    if not seats[seat_num]:
        emit('error', {'msg': '座位已被選'})
        return
    if user_id in user_selections:
        emit('error', {'msg': '您已選過座位，請先取消'})
        return
    seats[seat_num] = False
    user_selections[user_id] = seat_num
    emit('seat_update', {'seat_num': seat_num, 'status': False}, broadcast=True)
    emit('selection_success', {'seat_num': seat_num})

@socketio.on('cancel_seat')
@login_required
def on_cancel_seat(data):
    user_id = current_user.id
    if user_id not in user_selections:
        emit('error', {'msg': '您尚未選擇座位'})
        return
    seat_num = user_selections.pop(user_id)
    seats[seat_num] = True
    emit('seat_update', {'seat_num': seat_num, 'status': True}, broadcast=True)
    emit('cancel_success')

@app.route('/qrcode')
@login_required
def get_qrcode():
    user_id = current_user.id
    if user_id not in user_selections:
        return "尚未選擇座位", 400
    seat_num = user_selections[user_id]
    info = f"姓名:{users[user_id]['name']}, 座位:{seat_num}"
    img_io = generate_qrcode(info)
    return send_file(img_io, mimetype='image/png')

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)