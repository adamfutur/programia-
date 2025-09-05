from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

class CodingAgent:
    def __init__(self, model_name: str = "gpt-4.1-mini"):
        print("[INIT] Initializing CodingAgent")
        
        self.llm = ChatOpenAI(
            model="gpt-4.1-mini",
        )

        # Write your agent implementation here

if __name__ == "__main__":
    load_dotenv()
    print("[MAIN] Running CodingAgent")
    agent = CodingAgent()
    print("[MAIN] Completed running CodingAgent")
