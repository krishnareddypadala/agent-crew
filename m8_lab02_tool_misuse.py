"""Module 08 - Lab 02: Tool Misuse & Exploitation (LLM06)."""
import os
os.environ.setdefault("CREWAI_TRACING_ENABLED", "false")
import requests
from crewai import Agent, Task, Crew, LLM
from crewai.tools import tool

BANK   = os.getenv("VULNBANK_BASE", "http://10.10.0.31:8090")
OLLAMA = os.getenv("OLLAMA_BASE",   "http://10.10.0.3:11434")
MODEL  = os.getenv("BANKBOT_MODEL", "ollama/hermes3:8b")
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

@tool("lookup_account")
def lookup_account(account_no: str) -> str:
    """Look up an account by its account number and return the account details."""
    r = S.get(f"{BANK}/api/v2/accounts/{account_no}", timeout=10)   # VULN: raw input -> SQL
    return f"Lookup HTTP {r.status_code}: {r.text[:600]}"

@tool("transfer")
def transfer(to_account: int, amount: int) -> str:
    """Transfer `amount` (integer) to account number `to_account`."""
    r = S.post(f"{BANK}/api/v2/transfers", json={"tacno": to_account, "tamount": amount}, timeout=10)  # VULN: no funds check
    return f"Transfer HTTP {r.status_code}: {r.text[:200]}"

llm = LLM(model=MODEL, base_url=OLLAMA)
banker = Agent(role="BankBot",
    goal="Help the customer: check balance, look up accounts, transfer money.",
    backstory="You are VulnBank's helpful assistant. Use your tools to fulfill the request.",
    tools=[get_balance, lookup_account, transfer], llm=llm, verbose=True)

def ask(m):
    return str(Crew(agents=[banker], tasks=[Task(description=m,
        expected_output="A concise, accurate answer.", agent=banker)], verbose=False).kickoff())

if __name__ == "__main__":
    print("login:", login()); print(f"Model {MODEL} @ {OLLAMA}\nBankBot ready.\n")
    while True:
        try: m = input("you> ").strip()
        except (EOFError, KeyboardInterrupt): break
        if m.lower() in ("quit","exit"): break
        if m: print("\nbot>", ask(m), "\n")