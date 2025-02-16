from fastapi import FastAPI
from groq import Groq
from dotenv import load_dotenv
import elastic_db as db
import os
import uvicorn

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

groq_client = Groq(
    api_key=GROQ_API_KEY,
)

app = FastAPI()

# Pass ticker
# return: actual prices(price array) and predicted prices(array)
@app.get("/api/datapoints")
def get_data_points(ticker):
    return {[], []}

# pass ticker and user info
# return response
@app.get("/api/analysis")
def get_response(ticker):

    documents_string = db.search_documents(prompt)

    system_prompt = documents_string + algo_data + user_info + """\n

        You are a financial analyst with access to a varity of news articles and related documents. 
        You will use the above article summaries (facts and opinions) to conduct a through analysis 
        of the user given company, or to answer the user question. Additionally, tie your analysis
        with the data provided by our quantum computing algorithm. If there is a discrepency, mention
        it. Finally, ensure all your answers align in complexity with the given age group of the user.

    """

    chat_completion = groq_client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
        ],
        model="deepseek-r1-distill-llama-70b",
    )

    return response

# pass ticker and user info and prompt
# return response
@app.get("/api/prompt")
def get_response(ticker):
    return "dummy response for prompt call"

# 5 articles
# user info
# data points
# system prompt
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=False)