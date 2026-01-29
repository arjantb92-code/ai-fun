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

    def to_dict(self):
        """Serialize user to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "avatar_url": self.avatar_url,
            "is_group_member": self.is_group_member
        }

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

    def to_dict(self, include_stats=False):
        """
        Serialize trip/activity to dictionary.
        
        Args:
            include_stats: Whether to include transaction_count and total_amount
        """
        data = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "color": self.color,
            "icon": self.icon,
            "is_active": self.is_active,
            "archived_at": self.archived_at.isoformat() if self.archived_at else None,
        }
        return data

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

    def to_dict(self, include_transactions=True, include_results=True):
        """
        Serialize settlement session to dictionary.
        
        Args:
            include_transactions: Whether to include transactions
            include_results: Whether to include settlement results
        """
        total = sum(h.amount for h in self.results)
        data = {
            "id": self.id,
            "date": self.date.isoformat() if self.date else None,
            "description": self.description,
            "total_amount": round(total, 2),
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }
        if include_results:
            data["results"] = [r.to_dict() for r in self.results]
        if include_transactions:
            txs = sorted(self.transactions, key=lambda t: (t.date, t.time or ""))
            data["transactions"] = [
                {
                    "id": t.id,
                    "date": t.date.isoformat(),
                    "time": t.time,
                    "amount": round(t.amount, 2),
                    "description": t.description,
                    "payer": t.payer.name if t.payer else None
                }
                for t in txs
            ]
        return data

class Transaction(db.Model):
    __tablename__ = "transactions"
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.String(10), nullable=True, default="00:00")
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(255), nullable=False)
    payer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    type = db.Column(db.String(20), default="EXPENSE")
    category = db.Column(db.String(50), nullable=True, default="overig")
    receipt_url = db.Column(db.String(255), nullable=True)
    settlement_session_id = db.Column(db.Integer, db.ForeignKey("settlement_sessions.id"), nullable=True)
    trip_id = db.Column(db.Integer, db.ForeignKey("trips.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    deleted_at = db.Column(db.DateTime, nullable=True)

    payer = db.relationship("User", backref="paid_transactions", foreign_keys=[payer_id])
    splits = db.relationship("TransactionSplit", backref="transaction", cascade="all, delete-orphan")

    def to_dict(self, include_splits=True):
        """
        Serialize transaction to dictionary.
        
        Args:
            include_splits: Whether to include splits in output (default: True)
        """
        data = {
            "id": self.id,
            "date": self.date.isoformat(),
            "time": self.time or "00:00",
            "description": self.description,
            "amount": self.amount,
            "type": self.type or "EXPENSE",
            "category": self.category or "overig",
            "payer_id": self.payer_id,
            "activity_id": self.trip_id,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }
        if include_splits:
            data["splits"] = [s.to_dict() for s in self.splits]
        return data

class TransactionSplit(db.Model):
    __tablename__ = "transaction_splits"
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.Integer, db.ForeignKey("transactions.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    weight = db.Column(db.Integer, default=1)

    user = db.relationship("User")

    def to_dict(self):
        """Serialize split to dictionary."""
        return {
            "user_id": self.user_id,
            "weight": self.weight
        }

class HistoricalSettlement(db.Model):
    __tablename__ = "historical_settlements"
    id = db.Column(db.Integer, primary_key=True)
    settlement_session_id = db.Column(db.Integer, db.ForeignKey("settlement_sessions.id"), nullable=False)
    from_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    to_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    
    from_user = db.relationship("User", foreign_keys=[from_user_id])
    to_user = db.relationship("User", foreign_keys=[to_user_id])

    def to_dict(self):
        """Serialize historical settlement to dictionary."""
        return {
            "from_user": self.from_user.name if self.from_user else None,
            "to_user": self.to_user.name if self.to_user else None,
            "from_user_id": self.from_user_id,
            "to_user_id": self.to_user_id,
            "amount": round(self.amount, 2)
        }
