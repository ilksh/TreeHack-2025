import requests
import datetime
import json
import pandas as pd
from newspaper import Article
from groq import Groq
from openai import OpenAI
import tiktoken
import time
import random
from dotenv import load_dotenv
from tqdm import tqdm

ALPHAVANTAGE_API_KEY="NMTB928VTHVNY6J3 "
GROQ_API_KEY="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"
EMBEDDINGS_API_KEY="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"

groq_client = Groq(
    api_key=GROQ_API_KEY,
)

OpenAI.api_key = EMBEDDINGS_API_KEY 
embeddings_client = OpenAI()

BASE_URL = "https://www.alphavantage.co/query"
DAYS_BACK = 14

def truncate_text(text, max_tokens=8192):
    tokenizer = tiktoken.get_encoding("cl100k_base")
    tokens = tokenizer.encode(text)

    if len(tokens) > max_tokens:
        tokens = tokens[:max_tokens]

    return tokenizer.decode(tokens)


def exponential_backoff(error, retries, base_delay=1, max_delay=32, jitter=True):
    delay = min(base_delay * (2 ** retries), max_delay)
        
    if jitter:
        delay *= random.uniform(0.8, 1.2)

    print(f"Attempt {retries}:\n\n{error}\n\nSleeping for {delay:.2f} seconds...")
        
    time.sleep(delay)


def collect_articles(ticker):
    end_date = datetime.datetime.utcnow()
    start_date = end_date - datetime.timedelta(days=DAYS_BACK)
    params = {
        "function": "NEWS_SENTIMENT",
        "tickers": ticker,
        "apikey": ALPHAVANTAGE_API_KEY,
        "time_from": start_date.strftime("%Y%m%dT%H%M"),
        "sort": "RELEVANCE",
        "limit": 1000
    }

    response = requests.get(BASE_URL, params=params)
    return response.json()


def scrape_article(url):
    attempt = 0
    try:
        attempt += 1
        article = Article(url)
        article.download()
        article.parse()
    except Exception as e:
        exponential_backoff(e, attempt)

    return article.text


def digest_article(text):
    chat_completion = groq_client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "# You help a fellow LLM understand articles. List facts and opinions illustrated in the article:\n\n"
            },
            {
                "role": "user",
                "content": text
            },
            
        ],
        model="llama-3.1-8b-instant",
    )

    return chat_completion.choices[0].message.content


def embed_article(text):
    refined = truncate_text(text)
    response = embeddings_client.embeddings.create(
        input=refined,
        model="text-embedding-3-small"
    )

    return response.data[0].embedding


def main():

    try:
        df = pd.read_csv("newlog.csv")
        if df.empty:
            raise Exception("Empty log...")
    except Exception as e:
        print(e)
        df = pd.read_csv("newlog.csv")

    pbar = tqdm(total=df.shape[0])

    for symbol, security in zip(df["Symbol"], df["Security"]):
        
        articles = collect_articles(symbol)

        relevant_articles = []

        if articles.get("Information") is not None:
            print("Out of juice")
            print(articles)
            exit

        for article in articles["feed"]:

            document = {
                "company_name": security,
                "ticker_name": symbol,
                "url": article["url"],
                "sentiment_label": None,
                "relevance_score": None,
                "chatbot_digest": None,
                "embedding": None
            }

            for company in article.get("ticker_sentiment", []):
                if company.get("ticker") == symbol:

                    if float(company["relevance_score"]) < 0.1:
                        break

                    document["relevance_score"] = company.get("relevance_score")
                    document["sentiment_label"] = company.get("ticker_sentiment_label")

            else:

                text = scrape_article(article["url"])

                document["chatbot_digest"] = digest_article(text)
                document["embedding"] = embed_article(text)

                try:
                    with open(f"{symbol}.json", "r") as file:
                        data = json.load(file)
                        if not isinstance(data, list):
                            data = []
                except (FileNotFoundError, json.JSONDecodeError):
                    data = []

                data.append(document)

                with open(f"{symbol}.json", "w", encoding="utf-8") as file:
                    json.dump(data, file, indent=4)


                continue
            break

        df = df.iloc[1:]
        df.to_csv("newlog.csv", index=False)

        pbar.update(1)

if __name__ == "__main__":
    main()
    