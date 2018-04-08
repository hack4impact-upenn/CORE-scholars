import random
from faker import Faker
from . import User
from .. import db
from sqlalchemy.orm import validates


class SavingsHistory(db.Model):
    __tablename__ = 'savings_history'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    date = db.Column(db.String(64), index = True)
    balance = db.Column(db.Integer, index = True)
