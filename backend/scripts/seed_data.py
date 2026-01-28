import requests
import random
from datetime import datetime, timedelta

BASE_URL = "http://127.0.0.1:5000"

descriptions = [
    "Dinner at Loetje", "Groceries Lidl", "Cinema Tickets", "Fuel Shell", 
    "Pizza Night", "Coffee at Starbucks", "Bowling", "Train Tickets NS",
    "Concert Tickets", "Drinks at Rooftop Bar", "Uber Ride", "Lunch at Bagels & Beans",
    "Museum Entrance", "Snacks for Roadtrip", "Parking Fee Amsterdam"
]

users = [1, 2, 3]
all_users = [1, 2, 3, 4]

def seed_transactions():
    for i in range(15):
        payer_id = random.choice(users)
        amount = round(random.uniform(5.0, 120.0), 2)
        desc = descriptions[i % len(descriptions)]
        date = (datetime.now() - timedelta(days=random.randint(0, 30))).strftime('%Y-%m-%d')
        
        num_participants = random.randint(2, 4)
        participants = random.sample(all_users, num_participants)
        
        splits = []
        for u_id in participants:
            weight = random.choices([1, 2], weights=[0.8, 0.2])[0]
            splits.append({"user_id": u_id, "weight": weight})
            
        payload = {
            "description": desc,
            "amount": amount,
            "date": date,
            "payer_id": payer_id,
            "splits": splits
        }
        
        response = requests.post(f"{BASE_URL}/transactions", json=payload)
        if response.status_code == 200:
            print(f"Added: {desc} (€{amount})")
        else:
            print(f"Failed: {desc}")

if __name__ == "__main__":
    seed_transactions()
