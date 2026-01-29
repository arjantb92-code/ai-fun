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

class Trip(db.Model):
    __tablename__ = "trips"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    is_settled = db.Column(db.Boolean, default=False)
    color = db.Column(db.String(7), nullable=True)  # Hex color code
    icon = db.Column(db.String(10), nullable=True)  # Emoji/icon
    is_active = db.Column(db.Boolean, default=True)
    archived_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    transactions = db.relationship("Transaction", backref="trip", lazy="dynamic")

class SettlementSession(db.Model):
    __tablename__ = "settlement_sessions"
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    description = db.Column(db.String(255), nullable=True)
    trip_id = db.Column(db.Integer, db.ForeignKey("trips.id"), nullable=True)
    deleted_at = db.Column(db.DateTime, nullable=True)
    
    trip = db.relationship("Trip", backref="settlement_sessions")
    transactions = db.relationship("Transaction", backref="settlement_session")
    results = db.relationship("HistoricalSettlement", backref="session")

class Transaction(db.Model):
    __tablename__ = "transactions"
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.String(10), nullable=True, default="00:00")
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(255), nullable=False)
    payer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    type = db.Column(db.String(20), default="EXPENSE")
    receipt_url = db.Column(db.String(255), nullable=True)
    settlement_session_id = db.Column(db.Integer, db.ForeignKey("settlement_sessions.id"), nullable=True)
    trip_id = db.Column(db.Integer, db.ForeignKey("trips.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    deleted_at = db.Column(db.DateTime, nullable=True)

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
    payment_requests = db.relationship("PaymentRequest", backref="settlement", lazy="dynamic")


class PaymentRequest(db.Model):
    """
    Tracks Tikkie/iDEAL payment requests for settlements.
    
    Links a HistoricalSettlement to a Tikkie payment request,
    allowing users to pay their share via iDEAL.
    """
    __tablename__ = "payment_requests"
    id = db.Column(db.Integer, primary_key=True)
    
    # Link to the settlement this payment is for
    settlement_id = db.Column(db.Integer, db.ForeignKey("historical_settlements.id"), nullable=False)
    
    # Tikkie API fields
    tikkie_token = db.Column(db.String(100), unique=True, nullable=False)  # paymentRequestToken
    tikkie_url = db.Column(db.String(500), nullable=False)  # The payment URL
    amount_cents = db.Column(db.Integer, nullable=False)  # Amount in cents
    description = db.Column(db.String(255), nullable=True)
    
    # Status tracking
    # DEMO = demo mode, OPEN = awaiting payment, PAID = completed, EXPIRED = expired, CLOSED = manually closed
    status = db.Column(db.String(20), default="OPEN")
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)
    paid_at = db.Column(db.DateTime, nullable=True)
    
    # Payment info (filled when paid)
    payer_name = db.Column(db.String(100), nullable=True)  # Name from iDEAL
    
    @property
    def amount(self) -> float:
        """Amount in euros"""
        return self.amount_cents / 100.0
    
    @property
    def is_demo(self) -> bool:
        """Check if this is a demo payment request"""
        return self.status == "DEMO"
    
    @property
    def is_paid(self) -> bool:
        """Check if this payment has been completed"""
        return self.status == "PAID"
    
    @property
    def is_expired(self) -> bool:
        """Check if this payment request has expired"""
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return True
        return self.status == "EXPIRED"
