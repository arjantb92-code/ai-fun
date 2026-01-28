import requests
from bs4 import BeautifulSoup


def scrape_news(url="https://news.ycombinator.com/"):
    print(f"Scraping {url}...")
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        stories = soup.find_all("span", class_="titleline")

        print("\nTop stories on Hacker News:")
        for i, story in enumerate(stories[:10], 1):
            title_link = story.find("a")
            if title_link:
                print(f"{i}. {title_link.text}")

    except Exception as e:
        print(f"Error scraping: {e}")


if __name__ == "__main__":
    scrape_news()
