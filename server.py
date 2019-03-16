import sqlite3
from flask import Flask

from wtforms import PasswordField, SubmitField, StringField
from wtforms.validators import DataRequired
from flask_wtf import FlaskForm

from flask_restful import reqparse, abort, Api, Resource

from werkzeug.security import generate_password_hash

from flask_sqlalchemy import SQLAlchemy

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


class PostModel:
    def __init__(self, connection):
        self.connection = connection

    def insert(self, content, tred_id, user_id):
        user = User.query.filter_by(id=user_id).first()
        tred = Tred.query.filter_by(id=tred_id).first()
        note = Note(text=content, date=datetime.datetime.now())
        user.notes.append(note)
        tred.notes.append(note)
        db.session.commit()

    

db.create_all()
db.session.commit()
