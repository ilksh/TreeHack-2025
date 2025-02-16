from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from groq import Groq
from dotenv import load_dotenv
import elastic_db as db
import os
import uvicorn

# Load environment variables
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Initialize Groq LLM client
groq_client = Groq(api_key=GROQ_API_KEY)

app = FastAPI()

# Request body model
class ChatRequest(BaseModel):
    messages: list

@app.post("/api/chat")
async def chat(request: ChatRequest):

    if not request.messages:
        raise HTTPException(status_code=400, detail="No messages provided")

    user_input = request.messages[-1]["content"]

    company, ticker = db.gather_info(user_input)

    documents_string = db.search_documents(user_input, company, ticker)

    algo_data = ""
    if ticker:
        try:
            algo_data = db.get_forecast(ticker)
        except:
            pass

    user_info = "The user is a 23 year old novice investor.\n"

    system_prompt = documents_string + algo_data + user_info + """\n

        You are a financial analyst with access to a varity of news articles and related documents. 
        You will use the above article summaries (facts and opinions) to conduct a through analysis 
        of the user given company, or to answer the user question. Additionally, tie your analysis
        with the data provided by our quantum computing algorithm. If there is a discrepency, mention
        it. Finally, ensure all your answers align in complexity with the given age group of the user.

    """

    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_input
                },
            ],
            model="deepseek-r1-distill-llama-70b",
        )

        response_text = chat_completion.choices[0].message.content

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Groq API Error: {str(e)}")

    print(response_text)

    return {"response": response_text}

# Dummy endpoints (if needed)
@app.get("/api/datapoints")
def get_data_points(ticker: str):
    return {[], []}  

@app.get("/api/prompt")
def get_prompt_response(ticker: str):
    return "dummy response for prompt call"

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
