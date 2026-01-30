"""
Settlement calculation service.
Handles debt simplification and settlement suggestions.
"""
from models import User


class SettlementService:
    """Service for calculating settlement suggestions."""

    @staticmethod
    def calculate_suggestions(balances, user_map=None):
        """
        Calculate minimum payments to settle all debts.
        Uses greedy algorithm for debt simplification.
        
        Args:
            balances: dict of {user_id: balance}
            user_map: Optional dict of {user_id: user_name}
            
        Returns:
            list: Settlement suggestions [{from_user_id, from_user, to_user_id, to_user, amount}, ...]
        """
        if user_map is None:
            users = User.query.all()
            user_map = {u.id: u.name for u in users}
        
        # Split into debtors (negative balance) and creditors (positive balance)
        # Using 0.01 threshold to avoid floating point issues
        debtors = [
            [uid, abs(bal)] 
            for uid, bal in balances.items() 
            if bal < -0.01
        ]
        creditors = [
            [uid, bal] 
            for uid, bal in balances.items() 
            if bal > 0.01
        ]
        
        # Sort by amount (highest first) for optimal matching
        debtors.sort(key=lambda x: x[1], reverse=True)
        creditors.sort(key=lambda x: x[1], reverse=True)
        
        suggestions = []
        d_idx, c_idx = 0, 0
        
        # Greedy matching: match highest debtor with highest creditor
        while d_idx < len(debtors) and c_idx < len(creditors):
            # Amount to transfer is minimum of debt and credit
            amount = min(debtors[d_idx][1], creditors[c_idx][1])
            
            suggestions.append({
                "from_user_id": debtors[d_idx][0],
                "from_user": user_map.get(debtors[d_idx][0], "Unknown"),
                "to_user_id": creditors[c_idx][0],
                "to_user": user_map.get(creditors[c_idx][0], "Unknown"),
                "amount": round(amount, 2)
            })
            
            # Update remaining amounts
            debtors[d_idx][1] -= amount
            creditors[c_idx][1] -= amount
            
            # Move to next debtor/creditor if fully matched
            if debtors[d_idx][1] < 0.01:
                d_idx += 1
            if creditors[c_idx][1] < 0.01:
                c_idx += 1
        
        return suggestions

    @staticmethod
    def has_outstanding_balances(balances):
        """
        Check if there are any outstanding balances to settle.
        
        Args:
            balances: dict of {user_id: balance}
            
        Returns:
            bool: True if there are debts/credits to settle
        """
        for bal in balances.values():
            if abs(bal) > 0.01:
                return True
        return False
