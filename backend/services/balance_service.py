"""
Balance calculation service.
Centralizes all balance-related calculations to avoid code duplication.
"""
from models import User, Transaction


class BalanceService:
    """Service for calculating user balances from transactions."""

    @staticmethod
    def calculate_balances(transactions, users=None):
        """
        Calculate balance per user based on transactions.
        
        Positive balance = user is owed money (credit)
        Negative balance = user owes money (debt)
        
        Args:
            transactions: List of Transaction objects
            users: Optional list of User objects (fetched if not provided)
            
        Returns:
            dict: {user_id: balance} mapping with rounded values
        """
        if users is None:
            users = User.query.all()
        
        balances = {u.id: 0.0 for u in users}
        
        for tx in transactions:
            amount = tx.amount
            tx_type = tx.type or "EXPENSE"
            
            # Payer gets credit for paying
            if tx.payer_id in balances:
                if tx_type in ["EXPENSE", "TRANSFER"]:
                    balances[tx.payer_id] += amount
                else:  # INCOME
                    balances[tx.payer_id] -= amount
            
            # Calculate split distribution
            total_weight = sum(s.weight for s in tx.splits)
            if total_weight > 0:
                per_weight = amount / total_weight
                for split in tx.splits:
                    if split.user_id in balances:
                        if tx_type in ["EXPENSE", "TRANSFER"]:
                            balances[split.user_id] -= per_weight * split.weight
                        else:  # INCOME
                            balances[split.user_id] += per_weight * split.weight
        
        return {uid: round(bal, 2) for uid, bal in balances.items()}

    @staticmethod
    def get_unsettled_transactions(activity_id=None):
        """
        Get all unsettled, non-deleted transactions.
        
        Args:
            activity_id: Optional activity/trip ID to filter by
            
        Returns:
            list: List of Transaction objects
        """
        query = Transaction.query.filter_by(settlement_session_id=None)
        query = query.filter(Transaction.deleted_at.is_(None))
        if activity_id is not None:
            query = query.filter_by(trip_id=activity_id)
        return query.all()

    @staticmethod
    def format_balances_response(balances):
        """
        Format balances dict for JSON response.
        
        Args:
            balances: dict of {user_id: balance}
            
        Returns:
            list: [{user_id, balance}, ...]
        """
        return [
            {"user_id": uid, "balance": bal}
            for uid, bal in balances.items()
        ]
