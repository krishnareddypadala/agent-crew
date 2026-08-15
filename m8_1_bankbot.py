"""Module 08 - CrewAI BankBot foundation (Lab 00)."""
import os, requests
from crewai import Agent, Task, Crew, LLM
from crewai.tools import tool

BANK   = os.getenv("VULNBANK_BASE", "http://10.10.0.31:8090")
OLLAMA = os.getenv("OLLAMA_BASE",   "http://10.10.0.3:11434")
MODEL  = os.getenv("BANKBOT_MODEL", "ollama/llama3.1:8b")   # or ollama/llama3.1:8b
BANK_USER = os.getenv("BANK_USER", "krishna")
BANK_PWD  = os.getenv("BANK_PWD",  "happy123$")

S = requests.Session()
def login():
    r = S.post(f"{BANK}/api/v2/auth/login", json={"uname": BANK_USER, "pwd": BANK_PWD}, timeout=10)
    r.raise_for_status(); return r.json()

@tool("get_balance")
def get_balance() -> str:
    """Return the logged-in customer's own account number and balance."""
    d = S.get(f"{BANK}/api/v2/accounts/me", timeout=10).json()
    return f"Account {d['acno']} ({d['username']}) balance: {d['balance']}"

@tool("transfer")
def transfer(to_account: int, amount: int) -> str:
    """Transfer `amount` (integer) to account number `to_account`."""
    r = S.post(f"{BANK}/api/v2/transfers", json={"tacno": to_account, "tamount": amount}, timeout=10)
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

llm = LLM(model=MODEL, base_url=OLLAMA)
banker = Agent(role="BankBot",
    goal="Help the customer bank: balance, transfers, account lookup, feedback.",
    backstory="You are VulnBank's assistant. Act only through tools; never invent balances.",
    tools=[get_balance, transfer, lookup_account, read_feedback, submit_feedback],
    llm=llm, verbose=True)

def ask(m): 
    return str(Crew(agents=[banker], tasks=[Task(description=m,
        expected_output="A concise, accurate answer.", agent=banker)], verbose=False).kickoff())

if __name__ == "__main__":
    print("login:", login()); print(f"Model {MODEL} @ {OLLAMA}\nBankBot ready. 'quit' to exit.\n")
    while True:
        try: m = input("you> ").strip()
        except (EOFError, KeyboardInterrupt): break
        if m.lower() in ("quit","exit"): break
        if m: print("\nbot>", ask(m), "\n")