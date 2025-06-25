from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class ChatSession(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(36), db.ForeignKey('chat_session.id'), nullable=False)
    message_type = db.Column(db.String(10), nullable=False)  # 'user' or 'bot'
    content = db.Column(db.Text, nullable=False)
    plant_data = db.Column(db.Text)  # JSON string for plant identification results
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    session = db.relationship('ChatSession', backref=db.backref('messages', lazy=True, order_by='ChatMessage.timestamp'))