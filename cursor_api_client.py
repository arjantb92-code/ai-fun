import os
import requests
import json
import sys

CURSOR_AUTO_URL = "http://127.0.0.1:32123/v1/chat/completions"


def call_cursor_auto(prompt):
    headers = {"Content-Type": "application/json"}
    data = {"model": "auto", "messages": [{"role": "user", "content": prompt}]}
    try:
        response = requests.post(
            CURSOR_AUTO_URL, headers=headers, json=data, timeout=30
        )
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            return f"Error from Cursor Auto: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Failed to connect to Cursor Auto: {e}"


if __name__ == "__main__":
    if len(sys.argv) > 1:
        prompt = sys.argv[1]
        print(call_cursor_auto(prompt))
    else:
        print("Usage: python cursor_api_client.py \"Your prompt here\"")