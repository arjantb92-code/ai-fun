"""
Tikkie API Service for iDEAL Payment Integration

Tikkie is ABN AMRO's payment request service that uses iDEAL for payments.
This service provides integration with the Tikkie API for creating payment requests.

API Documentation: https://developer.abnamro.com/api-products/tikkie
Sandbox: https://api-sandbox.abnamro.com/v1/tikkie
Production: https://api.abnamro.com/v1/tikkie

Setup Requirements:
1. Register at https://developer.abnamro.com/
2. Create an app and get API Key (Consumer Key)
3. Generate app token (one-time) using your certificate
4. For production: Link to business ABN AMRO account
5. Set environment variables:
   - TIKKIE_API_KEY: Your consumer key
   - TIKKIE_APP_TOKEN: Your app token
   - TIKKIE_SANDBOX: "true" for sandbox, "false" for production
"""

import os
import uuid
import requests
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass


@dataclass
class TikkiePaymentRequest:
    """Represents a Tikkie payment request"""
    payment_request_token: str
    url: str
    amount_in_cents: int
    description: str
    reference_id: str
    created_at: datetime
    expiry_date: datetime
    status: str  # OPEN, PAID, CLOSED, EXPIRED


@dataclass
class TikkiePayment:
    """Represents a completed Tikkie payment"""
    payment_token: str
    amount_in_cents: int
    paid_at: datetime
    payer_name: Optional[str]


class TikkieService:
    """
    Service for creating and managing Tikkie payment requests.
    
    Works in three modes:
    1. DEMO mode (default): No real API calls, generates mock URLs for development
    2. SANDBOX mode: Uses ABN AMRO sandbox API for testing
    3. PRODUCTION mode: Uses real ABN AMRO API
    """
    
    SANDBOX_BASE_URL = "https://api-sandbox.abnamro.com/v2/tikkie"
    PRODUCTION_BASE_URL = "https://api.abnamro.com/v2/tikkie"
    
    def __init__(self):
        self.api_key = os.getenv("TIKKIE_API_KEY")
        self.app_token = os.getenv("TIKKIE_APP_TOKEN")
        self.sandbox = os.getenv("TIKKIE_SANDBOX", "true").lower() == "true"
        self._demo_mode = not self.api_key or not self.app_token
        
    @property
    def base_url(self) -> str:
        return self.SANDBOX_BASE_URL if self.sandbox else self.PRODUCTION_BASE_URL
    
    @property
    def is_demo_mode(self) -> bool:
        """Check if running in demo mode (no API credentials configured)"""
        return self._demo_mode
    
    def _get_headers(self) -> dict:
        """Get authentication headers for API requests"""
        return {
            "API-Key": self.api_key,
            "X-App-Token": self.app_token,
            "Content-Type": "application/json"
        }
    
    def create_payment_request(
        self,
        amount_cents: int,
        description: str,
        reference_id: str,
        expiry_days: int = 14
    ) -> TikkiePaymentRequest:
        """
        Create a new Tikkie payment request.
        
        Args:
            amount_cents: Amount in cents (e.g., 1000 for €10.00)
            description: Description shown to payer (max 35 chars for iDEAL)
            reference_id: Your internal reference (e.g., settlement_id_from_user_to_user)
            expiry_days: Days until the request expires (default 14)
            
        Returns:
            TikkiePaymentRequest with the payment URL
        """
        if self._demo_mode:
            return self._create_demo_payment_request(amount_cents, description, reference_id, expiry_days)
        
        expiry_date = datetime.utcnow() + timedelta(days=expiry_days)
        
        payload = {
            "amountInCents": amount_cents,
            "description": description[:35],  # iDEAL limit
            "externalId": reference_id,
            "expiryDate": expiry_date.strftime("%Y-%m-%d")
        }
        
        response = requests.post(
            f"{self.base_url}/paymentrequests",
            headers=self._get_headers(),
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        
        return TikkiePaymentRequest(
            payment_request_token=data["paymentRequestToken"],
            url=data["url"],
            amount_in_cents=amount_cents,
            description=description,
            reference_id=reference_id,
            created_at=datetime.utcnow(),
            expiry_date=expiry_date,
            status="OPEN"
        )
    
    def _create_demo_payment_request(
        self,
        amount_cents: int,
        description: str,
        reference_id: str,
        expiry_days: int
    ) -> TikkiePaymentRequest:
        """Create a demo payment request (no real API call)"""
        demo_token = f"DEMO-{uuid.uuid4().hex[:16].upper()}"
        # Generate a demo URL that shows what it would look like
        demo_url = f"https://tikkie.me/pay/DEMO/{demo_token}"
        
        return TikkiePaymentRequest(
            payment_request_token=demo_token,
            url=demo_url,
            amount_in_cents=amount_cents,
            description=description,
            reference_id=reference_id,
            created_at=datetime.utcnow(),
            expiry_date=datetime.utcnow() + timedelta(days=expiry_days),
            status="DEMO"  # Special status for demo mode
        )
    
    def get_payment_request(self, payment_request_token: str) -> Optional[TikkiePaymentRequest]:
        """
        Get the status of a payment request.
        
        Args:
            payment_request_token: The token returned when creating the request
            
        Returns:
            Updated TikkiePaymentRequest or None if not found
        """
        if self._demo_mode:
            # In demo mode, always return "OPEN" status
            return None
        
        response = requests.get(
            f"{self.base_url}/paymentrequests/{payment_request_token}",
            headers=self._get_headers(),
            timeout=30
        )
        
        if response.status_code == 404:
            return None
            
        response.raise_for_status()
        data = response.json()
        
        return TikkiePaymentRequest(
            payment_request_token=data["paymentRequestToken"],
            url=data["url"],
            amount_in_cents=data["amountInCents"],
            description=data.get("description", ""),
            reference_id=data.get("externalId", ""),
            created_at=datetime.fromisoformat(data["createdDateTime"].replace("Z", "+00:00")),
            expiry_date=datetime.fromisoformat(data["expiryDate"]),
            status=data["status"]
        )
    
    def get_payments(self, payment_request_token: str) -> list[TikkiePayment]:
        """
        Get all payments made for a payment request.
        
        A single payment request can have multiple payments (partial payments).
        
        Args:
            payment_request_token: The token of the payment request
            
        Returns:
            List of TikkiePayment objects
        """
        if self._demo_mode:
            return []
        
        response = requests.get(
            f"{self.base_url}/paymentrequests/{payment_request_token}/payments",
            headers=self._get_headers(),
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        
        payments = []
        for p in data.get("payments", []):
            payments.append(TikkiePayment(
                payment_token=p["paymentToken"],
                amount_in_cents=p["amountInCents"],
                paid_at=datetime.fromisoformat(p["paidDateTime"].replace("Z", "+00:00")),
                payer_name=p.get("counterPartyName")
            ))
        
        return payments
    
    def is_fully_paid(self, payment_request_token: str, expected_amount_cents: int) -> bool:
        """
        Check if a payment request has been fully paid.
        
        Args:
            payment_request_token: The token of the payment request
            expected_amount_cents: The expected total amount in cents
            
        Returns:
            True if fully paid, False otherwise
        """
        if self._demo_mode:
            return False
        
        payments = self.get_payments(payment_request_token)
        total_paid = sum(p.amount_in_cents for p in payments)
        return total_paid >= expected_amount_cents


def get_tikkie_service() -> TikkieService:
    """Get the Tikkie service instance"""
    return TikkieService()


# Example usage and setup instructions
SETUP_INSTRUCTIONS = """
=== Tikkie API Setup Instructions ===

1. REGISTER for ABN AMRO Developer Portal:
   - Go to https://developer.abnamro.com/
   - Create an account and log in
   - Subscribe to the Tikkie API product

2. CREATE an App:
   - In the developer portal, create a new app
   - Note your API Key (Consumer Key)

3. GENERATE App Token:
   - Follow ABN AMRO's documentation to generate an app token
   - This requires a one-time API call with your credentials

4. CONFIGURE Environment Variables:
   Add these to your .env file:
   
   TIKKIE_API_KEY=your-api-key-here
   TIKKIE_APP_TOKEN=your-app-token-here
   TIKKIE_SANDBOX=true  # Set to false for production

5. FOR PRODUCTION:
   - Your ABN AMRO business account must be linked
   - Complete the production onboarding process
   - Set TIKKIE_SANDBOX=false

Without these environment variables, the service runs in DEMO mode,
generating mock payment URLs for development purposes.
"""
