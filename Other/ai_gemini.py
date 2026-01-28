import os
import requests
import json
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from google import genai

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

PRIMARY_MODEL = "gemini-2.5-flash"
FALLBACK_GRAVITY_MODEL = "antigravity-gemini-3-flash"
CURSOR_AUTO_URL = "http://127.0.0.1:32123/v1/chat/completions"


def get_hn_context():
    try:
        response = requests.get("https://news.ycombinator.com/", timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        stories = soup.find_all("span", class_="titleline")
        titles = []
        for s in stories[:10]:
            a_tag = s.find("a")
            if a_tag:
                titles.append(a_tag.text)
        return "\n".join(titles)
    except Exception as e:
        return f"Could not fetch HN news: {e}"


def call_cursor_auto(prompt):
    print(f"\n--- Falling back to Cursor Agent Auto ---")
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


def generate_with_fallback(client, model, prompt):
    try:
        response = client.models.generate_content(model=model, contents=prompt)
        return response.text
    except Exception as e:
        error_msg = str(e).lower()
        if (
            "429" in error_msg
            or "quota" in error_msg
            or "limit" in error_msg
            or "restricted" in error_msg
        ):
            print(
                f"\n[Sisyphus] Primary model '{model}' limited/restricted. Error: {e}"
            )

            print(
                f"--- Falling back to Gravity Free Model: {FALLBACK_GRAVITY_MODEL} ---"
            )
            try:
                response = client.models.generate_content(
                    model=FALLBACK_GRAVITY_MODEL, contents=prompt
                )
                return response.text
            except Exception as e2:
                print(f"[Sisyphus] Gravity fallback failed. Error: {e2}")

                return call_cursor_auto(prompt)
        else:
            raise e


def run_ai_interaction():
    client = genai.Client(api_key=GEMINI_API_KEY)

    print("1. Standard Prompt")
    print("2. Summarize Hacker News (AI-Free Scraper Input)")
    choice = input("Select an option (1-2): ")

    if choice == "2":
        context = get_hn_context()
        prompt = f"Here are the top stories on Hacker News right now. Please summarize the current trends based on these titles:\n\n{context}"
        print("\n--- Scraped Data (AI-Free Input) ---")
        print(context)
        print("\n--- AI Response ---")
    else:
        prompt = input("Enter your prompt: ")

    try:
        result = generate_with_fallback(client, PRIMARY_MODEL, prompt)
        print(result)
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")


if __name__ == "__main__":
    run_ai_interaction()
