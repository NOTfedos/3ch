import sqlite3
from flask import Flask

from wtforms import PasswordField, SubmitField, StringField
from wtforms.validators import DataRequired
from flask_wtf import FlaskForm

from flask_restful import reqparse, abort, Api, Resource

from werkzeug.security import generate_password_hash

from flask_sqlalchemy import SQLAlchemy

from flask import jsonify

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


class User(db.Model):
    id = db.Column(db.Integer,  primary_key=True)
    username = db.Column(db.String(15), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    tag = db.Column(db.String(15), unique=False, nullable=False)
    activity = db.Column(db.Integer, nullable=False)
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


db.create_all()
db.session.commit()

session = {
    'username': None,
    'user_id': None
}
