import sqlite3
from flask import Flask

from wtforms import PasswordField, SubmitField, StringField, TextAreaField
from wtforms.validators import DataRequired
from flask_wtf import FlaskForm

from flask_restful import reqparse, abort, Api, Resource

from werkzeug.security import generate_password_hash

from flask_sqlalchemy import SQLAlchemy

from flask import jsonify
from flask import render_template
from flask import redirect

import datetime


app = Flask(__name__)
api = Api(app)
hash_sert = generate_password_hash('yandexlyceum')
app.config['SECRET_KEY'] = hash_sert
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///main.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class LoginForm(FlaskForm):
    username = StringField('Никнейм', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')


class AddTredForm(FlaskForm):
    topic = TextAreaField('Тема')
    submit = SubmitField('Добавить тред')


class AddNoteForm(FlaskForm):
    content = TextAreaField('Текст')
    submit = SubmitField('Добавить запись')


class RegisterForm(FlaskForm):
    username = StringField('Никнейм', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    email = StringField('e-mail', validators=[DataRequired()])
    submit = SubmitField('Зарегистрироваться')


class User(db.Model):
    id = db.Column(db.Integer,  primary_key=True)
    username = db.Column(db.String(15), unique=True, nullable=False)
    password = db.Column(db.String(20), unique=False, nullable=False)
    email = db.Column(db.String(120), unique=False, nullable=False)
    tag = db.Column(db.String(15), unique=False, nullable=False)
    treds = db.relationship('Tred', backref='user', lazy=True)
    notes = db.relationship('Note', backref='user', lazy=True)

    def __repr__(self):
        return 'User {} {}'.format(self.username, self.email)


class Tred(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    topic = db.Column(db.String(200), unique=True, nullable=False)
    date = db.Column(db.DateTime, unique=False, nullable=False)
    notes = db.relationship('Note', backref='tred', lazy=True)

    def __repr__(self):
        return 'Tred {} {}'.format(self.topic, self.user_id)


class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    tred_id = db.Column(db.Integer, db.ForeignKey('tred.id'), nullable=False)
    date = db.Column(db.DateTime, unique=False, nullable=False)
    text = db.Column(db.Text, unique=False, nullable=False)

    def __repr__(self):
        return 'Note {} {}'.format(self.tred_id, self.user_id)


class TredList(Resource):
    def get(self):
        treds = get_all_treds()
        return jsonify({'treds': treds})

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('topic', required=True)
        parser.add_argument('user_id', required=True, type=int)
        args = parser.parse_args()
        return tred_insert(args['topic'], args['user_id'])


class NoteList(Resource):
    def get(self, tred_id):
        notes = get_all_notes(tred_id)
        return jsonify({'notes': notes})

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('content', required=True)
        parser.add_argument('user_id', required=True, type=int)
        parser.add_argument('tred_id', required=True, type=int)
        args = parser.parse_args()
        return note_insert(args['content'], args['tred_id'], args['user_id'])


class Treds(Resource):
    def get(self, tred_id):
        abort_if_news_not_found_tred(tred_id)
        tred = get_tred(tred_id)
        return jsonify({'tred': tred})

    def delete(self, user_id, tred_id,):
        return tred_delete(user_id, tred_id)


class Notes(Resource):
    def get(self, note_id):
        abort_if_news_not_found_note(note_id)
        note = get_note(note_id)
        return jsonify({'note': note})

    def delete(self, user_id, note_id):
        return note_delete(user_id, note_id)


def note_insert(content, tred_id, user_id):
    user = get_user(user_id)
    if user is None:
        return jsonify({'error': 'User not found'})
    tred = get_tred(tred_id)
    if tred is None:
        return jsonify({'error': 'Tred not found'})
    note = Note(text=content, date=datetime.datetime.now())
    user.notes.append(note)
    tred.notes.append(note)
    db.session.commit()
    return jsonify({'success': 'OK'})


def tred_insert(topic, user_id):
    user = get_user(user_id)
    if user is None:
        return jsonify({'error': 'User not found'})
    tred = Tred(topic=topic, date=datetime.datetime.now())
    user.treds.append(tred)
    db.session.commit()
    return jsonify({'success': 'OK'})


def note_delete(user_id, note_id):
    # user = User.query.filter_by(id=user_id)
    note = get_note(note_id)
    if note is None:
        return jsonify({'error': 'Note not found'})
    if note.user_id == user_id:
        db.session.delete(note)
        db.session.commit()
        return jsonify({'success': 'OK'})
    else:
        return jsonify({'error': 'You dont have permission'})


def tred_delete(user_id, tred_id):
    tred = get_tred(tred_id)
    if tred is None:
        return jsonify({'error': 'Tred not found'})
    if tred.user_id == user_id:
        db.session.delete(tred)
        db.session.commit()
        return jsonify({'success': 'OK'})
    else:
        return jsonify({'error': 'You dont have permission'})


def get_note(note_id):
    return Note.query.filter_by(id=note_id).first()


def get_tred(tred_id):
    return Tred.query.filter_by(id=tred_id).first()


def get_user(user_id):
    return User.query.filter_by(id=user_id).first()


def get_all_treds():
    return Tred.query.all()


def get_all_notes(tred_id):
    return Note.query.filter_by(tred_id=tred_id).all()


def abort_if_news_not_found_tred(tred_id):
    if not get_tred(tred_id):
        abort(404, message="Tred {} not found".format(tred_id))


def abort_if_news_not_found_note(note_id):
    if not get_note(note_id):
        abort(404, message="Note {} not found".format(note_id))


def user_exists(user_name, password):
    user = User.query.filter_by(username=user_name).first()
    if user is None:
        return False
    if user.password == password:
        return True
    return False


def add_user(username, password, email, tag):
    user = User(username=username,
                password=password,
                email=email,
                tag=tag)
    db.session.add(user)
    db.session.commit()


db.create_all()
db.session.commit()

session = {
    'username': '',
    'user_id': ''
}

# api.add_resource(TredList, '/treds')
# api.add_resource(Treds, '/treds/<int:tred_id>')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user_name = form.username.data
        password = form.password.data
        if user_exists(user_name, password):
            session['username'] = user_name
            session['user_id'] = User.query.filter_by(username=user_name).first().id
            return redirect("/index")
    return render_template('login.html', title='Авторизация', form=form, username='')


@app.route('/logout')
def logout():
    session['username'], session['user_id'] = '', ''
    return redirect('/login')


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        user_name = form.username.data
        password = form.password.data
        email = form.email.data
        if not user_exists(user_name, password):
            add_user(user_name, password, email, 'alpha_tester')
            return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form, username='')


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', username=session['username'])


@app.route('/add-tred', methods=['GET', 'POST'])
def add_tred():
    if session['username'] == '':
        return redirect('/login')
    form = AddTredForm()
    if form.validate_on_submit():
        topic = form.topic.data
        tred_insert(topic, session['user_id'])
        return redirect('/treds')
    return render_template('add_tred.html', title='Добавление треда',
                           form=form, username=session['username'])


@app.route('/add-note/<int:tred_id>', methods=['GET', 'POST'])
def add_note(tred_id):
    if session['username'] == '':
        return redirect('/login')
    form = AddNoteForm()
    if form.validate_on_submit():
        content = form.content.data
        note_insert(content, tred_id, session['user_id'])
        return redirect('/treds/{}'.format(tred_id))
    return render_template('add_note.html', title='Добавление записи',
                           form=form, username=session['username'])


'''@app.route("/treds", endpoint='treds')
def treds():
    return render_template('treds.html', title='Треды',
                           treds=get_all_treds(), username=session['username'])'''


@app.route("/treds/<int:tred_id>", endpoint='tred_notes')
def tred_notes(tred_id):
    return render_template('notes.html',
                           title='Тред "{}"'.format(get_tred(tred_id).topic),
                           notes=get_all_notes(tred_id),
                           username=session['username'])


if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1')
