import os
import time
from dotenv import load_dotenv
from strands import Agent
from strands.models.litellm import LiteLLMModel
from tools import classify_waste, find_recyclers, estimate_value, get_impact_stats

load_dotenv()
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")

def create_agent():
    model = LiteLLMModel(
        model_id="groq/qwen/qwen3.8-27b",
        params={
            "temperature": 0.3,
            "max_tokens": 512,
            "stream": False
        }
    )
    agent = Agent(
        model=model,
        tools=[classify_waste, find_recyclers, estimate_value, get_impact_stats],
        system_prompt="""You are WasteWise, an AI waste management assistant for Indian households.

Your job:
1. Classify waste items users describe into categories (plastic, paper, cardboard, metal, ewaste, glass, wet, other)
2. Give clear disposal instructions for each item
3. Warn strongly about e-waste hazards - never burn or dump
4. Match users with nearby informal recyclers (kabadiwalas) based on their location
5. Estimate indicative value of recyclables (always label as sample rates, not live prices)
6. Show environmental impact of proper waste segregation

Rules:
- Always use the tools provided, do not guess classifications
- Always mention e-waste hazards clearly
- Be helpful, simple, and clear — users may not be tech-savvy
- Use INR for prices
- Never claim recycler data or prices are verified live data
- Encourage users to segregate waste at source
"""
    )
    return agent

def run_agent(agent, prompt, retries=3):
    for attempt in range(retries):
        try:
            return agent(prompt)
        except Exception as e:
            err = str(e).lower()
            if "rate_limit" in err or "quota" in err:
                wait = 20 * (attempt + 1)
                print(f"Rate limit hit. Waiting {wait}s...")
                time.sleep(wait)
            else:
                raise e
    raise Exception("Agent failed after retries.")

if __name__ == "__main__":
    agent = create_agent()
    print("WasteWise Agent ready. Type your waste query.")
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ["exit", "quit"]:
            break
        response = run_agent(agent, user_input)
        print(f"\nWasteWise: {response}")