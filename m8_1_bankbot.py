"""Module 08 - CrewAI BankBot foundation (Lab 00).

A single CrewAI agent with 5 tools that drive the phpvulnbank Laravel v2 API.
This is the clean baseline the attack labs (01-06) build on.

Run on a student box (WireGuard connected):
    python bankbot.py
Then chat, e.g.:
    you> what is my balance?
    you> transfer 10 to account 3
    you> look up account 2
"""
import os
os.environ.setdefault("CREWAI_TRACING_ENABLED", "false")  # keep the REPL clean (no trace prompt)
import requests
from crewai import Agent, Task, Crew, LLM
from crewai.tools import tool

# --- config (override via env) ---
BANK   = os.getenv("VULNBANK_BASE", "http://10.10.0.31:8090")   # bank over WireGuard
OLLAMA = os.getenv("OLLAMA_BASE",   "http://10.10.0.3:11434")   # Ollama on beast over WG
MODEL  = os.getenv("BANKBOT_MODEL", "ollama/qwen3:latest")      # or ollama/llama3.1:8b
BANK_USER = os.getenv("BANK_USER", "krishna")
BANK_PWD  = os.getenv("BANK_PWD",  "happy123$")

# --- one authenticated session shared by every tool (Laravel cookie auth) ---
S = requests.Session()

def login():
    r = S.post(f"{BANK}/api/v2/auth/login",
               json={"uname": BANK_USER, "pwd": BANK_PWD}, timeout=10)
    r.raise_for_status()
    return r.json()

# --- the 5 bank tools ---
@tool("get_balance")
def get_balance() -> str:
    """Return the logged-in customer's own account number and balance."""
    d = S.get(f"{BANK}/api/v2/accounts/me", timeout=10).json()
    return f"Account {d['acno']} ({d['username']}) balance: {d['balance']}"

@tool("transfer")
def transfer(to_account: int, amount: int) -> str:
    """Transfer `amount` (an integer) to account number `to_account`."""
    r = S.post(f"{BANK}/api/v2/transfers",
               json={"tacno": to_account, "tamount": amount}, timeout=10)
    return f"Transfer HTTP {r.status_code}: {r.text[:200]}"

@tool("lookup_account")
def lookup_account(account_no: str) -> str:
    """Look up any account by its account number and return its details."""
    r = S.get(f"{BANK}/api/v2/accounts/{account_no}", timeout=10)
    return f"Lookup HTTP {r.status_code}: {r.text[:400]}"

@tool("read_feedback")
def read_feedback() -> str:
    """Read all stored customer feedback."""
    return S.get(f"{BANK}/api/v2/feedback", timeout=10).text[:600]

@tool("submit_feedback")
def submit_feedback(text: str) -> str:
    """Save feedback `text` to the logged-in customer's profile."""
    r = S.put(f"{BANK}/api/v2/feedback/me", json={"fb": text}, timeout=10)
    return f"Feedback saved (HTTP {r.status_code})."

# --- the agent ---
llm = LLM(model=MODEL, base_url=OLLAMA)
banker = Agent(
    role="BankBot",
    goal="Help the customer bank: check balance, transfer money, look up accounts, manage feedback.",
    backstory=("You are the assistant for VulnBank. You act only through your tools and never "
               "invent balances or results. Report exactly what the tools return."),
    tools=[get_balance, transfer, lookup_account, read_feedback, submit_feedback],
    llm=llm,
    verbose=True,
)

def ask(message: str) -> str:
    task = Task(description=message,
                expected_output="A concise, accurate answer for the customer.",
                agent=banker)
    return str(Crew(agents=[banker], tasks=[task], verbose=False).kickoff())

if __name__ == "__main__":
    print(f"Logging in to {BANK} as {BANK_USER} ...")
    print("  ->", login())
    print(f"Model: {MODEL} @ {OLLAMA}")
    print("BankBot ready. Ask something, or type 'quit'.\n")
    while True:
        try:
            m = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if m.lower() in ("quit", "exit"):
            break
        if m:
            print("\nbot>", ask(m), "\n")
