from groq import Groq
from dotenv import load_dotenv
import elastic_db as db
import os

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

groq_client = Groq(
    api_key=GROQ_API_KEY,
)

def get_response(prompt):

    documents_string = db.search_documents(prompt)

    algo_data = db.get_forecast()

    user_info = "The user is a 23 year old novice investor.\n"

    system_prompt = documents_string + algo_data + user_info + """\n

        You are a financial analyst with access to a varity of news articles and related documents. 
        You will use the above article summaries (facts and opinions) to conduct a through analysis 
        of the user given company, or to answer the user question. Additionally, tie your analysis
        with the data provided by our quantum computing algorithm. If there is a discrepency, mention
        it. Finally, ensure all your answers align in complexity with the given age group of the user.

    """

    print(system_prompt)

    chat_completion = groq_client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": prompt
            },
        ],
        model="deepseek-r1-distill-llama-70b",
    )

    return chat_completion.choices[0].message.content

def main():
    print("What do you want gloober.")
    bruh = input()
    print(get_response(bruh))


if __name__ == "__main__":
    main()