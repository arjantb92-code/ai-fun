from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    avatar_url = db.Column(db.String(255), nullable=True)
    is_group_member = db.Column(db.Boolean, default=True)
    password_hash = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SettlementSession(db.Model):
    __tablename__ = "settlement_sessions"
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    description = db.Column(db.String(255), nullable=True)
    
    transactions = db.relationship("Transaction", backref="settlement_session")
    results = db.relationship("HistoricalSettlement", backref="session")

class Transaction(db.Model):
    __tablename__ = "transactions"
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(255), nullable=False)
    payer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    type = db.Column(db.String(20), default="EXPENSE") 
    receipt_url = db.Column(db.String(255), nullable=True)
    settlement_session_id = db.Column(db.Integer, db.ForeignKey("settlement_sessions.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    payer = db.relationship("User", backref="paid_transactions", foreign_keys=[payer_id])
    splits = db.relationship("TransactionSplit", backref="transaction", cascade="all, delete-orphan")

class TransactionSplit(db.Model):
    __tablename__ = "transaction_splits"
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.Integer, db.ForeignKey("transactions.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    weight = db.Column(db.Integer, default=1)

    user = db.relationship("User")

class HistoricalSettlement(db.Model):
    __tablename__ = "historical_settlements"
    id = db.Column(db.Integer, primary_key=True)
    settlement_session_id = db.Column(db.Integer, db.ForeignKey("settlement_sessions.id"), nullable=False)
    from_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    to_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    
    from_user = db.relationship("User", foreign_keys=[from_user_id])
    to_user = db.relationship("User", foreign_keys=[to_user_id])
