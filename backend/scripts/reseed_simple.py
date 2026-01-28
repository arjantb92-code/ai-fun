import requests

BASE_URL = "http://127.0.0.1:5000"

def reseed():
    # Login
    login_res = requests.post(f"{BASE_URL}/login", json={"username": "Arjan", "password": "wbw2026"})
    if login_res.status_code != 200:
        print("Login failed")
        return
    token = login_res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    txs = [
        {
            "description": "Dinner at Loetje",
            "amount": 90.00,
            "date": "2026-01-28",
            "payer_id": 1,
            "splits": [{"user_id": 1, "weight": 1}, {"user_id": 2, "weight": 1}, {"user_id": 3, "weight": 1}]
        },
        {
            "description": "AH Groceries",
            "amount": 30.00,
            "date": "2026-01-27",
            "payer_id": 2,
            "splits": [{"user_id": 1, "weight": 1}, {"user_id": 2, "weight": 1}]
        },
        {
            "description": "Beer & Snacks",
            "amount": 45.00,
            "date": "2026-01-26",
            "payer_id": 3,
            "splits": [{"user_id": 1, "weight": 2}, {"user_id": 3, "weight": 1}]
        }
    ]

    for tx in txs:
        res = requests.post(f"{BASE_URL}/transactions", json=tx, headers=headers)
        if res.status_code == 200:
            print(f"Added {tx['description']}")
        else:
            print(f"Failed {tx['description']}: {res.text}")

if __name__ == "__main__":
    reseed()
