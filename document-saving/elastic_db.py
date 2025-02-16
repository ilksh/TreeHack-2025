from elasticsearch import Elasticsearch
from openai import OpenAI
import pandas as pd
import json
from groq import Groq
from dotenv import load_dotenv
import os
import spacy

load_dotenv()

ELASTIC_API_KEY = os.getenv("ELASTIC_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
EMBEDDINGS_API_KEY = os.getenv("OPENAI_API_KEY")

es = Elasticsearch(
    "https://my-elasticsearch-project-e34bd6.es.us-west-2.aws.elastic.cloud:443",
    api_key=ELASTIC_API_KEY
)

groq_client = Groq(
    api_key=GROQ_API_KEY,
)

embeddings_client = OpenAI()

nlp = spacy.load("en_core_web_sm")

index_name = "treehacks-index"

mapping = {
    "mappings": {
        "properties": {
            "company_name": {"type": "keyword"},
            "ticker_name": {"type": "keyword"},
            "url": {"type": "keyword"},
            "sentiment_label": {"type": "keyword"},
            "relevance_score": {"type": "float"},
            "chatbot_digest": {"type": "text"},
            "embedding": {"type": "dense_vector", "dims": 1536}
        }
    }
}

if not es.indices.exists(index=index_name):
    es.indices.create(index=index_name, body=mapping)

def load_documents():

    df = pd.read_csv("constituents.csv")

    for symbol in df["Symbol"]:

        try:
            with open(f"tickers/{symbol}.json", "r") as file:
                data = json.load(file)
        except Exception as e:
            # print(e)
            continue

        for i, obj in enumerate(data):
            doc_id = f"{symbol}_{i}"
            es.index(index=index_name, id=doc_id, body=obj)


def search_documents(prompt):

    company = None

    doc = nlp(prompt)
    for ent in doc.ents:
        if ent.label_ == "ORG":
            company = ent.text

    chat_completion = groq_client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": f'# Determine whether the following question requires retrieving external data (RAG) or can be answered directly:\n\n"{prompt}"\n\nAnswer with only "RAG" or "NO RAG".'
            },
            {
                "role": "user",
                "content": prompt
            },
            
        ],
        model="llama-3.1-8b-instant",
        max_tokens=5
    )

    if chat_completion.choices[0].message.content == "NO RAG":
        return None

    print(chat_completion.choices[0].message.content)

    response = embeddings_client.embeddings.create(
        input=prompt,
        model="text-embedding-3-small"
    )

    query_vector = response.data[0].embedding

    search_query = {
        "size": 5,
        "query": {
            "script_score": {
                "query": {"match_all": {}},
                "script": {
                    "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                    "params": {"query_vector": query_vector}
                }
            }
        }
    }

    if company:
        search_query["query"]["script_score"]["query"] = {"match": {"company_name": company}}
    # else:
        # search_query["query"]["script_score"]["query"] = {"match_all": {}}

    search_response = es.search(index=index_name, body=search_query)

    combined = ""
    for response in search_response["hits"]["hits"]:
        combined += response["_source"]["chatbot_digest"] + "\n"

    return combined
    

def main():
    # load_documents()
    search_documents("How is AbbVie Inc doing in the news?")

if __name__ == "__main__":
    main()