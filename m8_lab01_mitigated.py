"""Module 08 - Lab 01 MITIGATED: enforce the policy in the TOOL, not the prompt.

Same restricted teller, same tools, same winning injection. The difference:
the read-only rule now lives in CODE (a server-side guard the model cannot argue
with), not in the backstory. Run the OpsBot persona-swap payload again -> the tool
refuses and the balance does NOT change, regardless of model or phrasing.

Two defenses shown:
  1) LEAST PRIVILEGE  - a read-only agent simply should not be handed a transfer tool.
  2) POLICY-IN-TOOL   - if it must have it, the tool enforces the rule itself.
This file demonstrates (2) so you can prove the same hijack now does nothing.
"""
import os
os.environ.setdefault("CREWAI_TRACING_ENABLED", "false")
import requests
from crewai import Agent, Task, Crew, LLM
from crewai.tools import tool

BANK   = os.getenv("VULNBANK_BASE", "http://10.10.0.31:8090")
OLLAMA = os.getenv("OLLAMA_BASE",   "http://10.10.0.3:11434")
MODEL  = os.getenv("BANKBOT_MODEL", "ollama/llama3.1:8b")   # deliberately the weak model
BANK_USER = os.getenv("BANK_USER", "krishna")
BANK_PWD  = os.getenv("BANK_PWD",  "happy123$")

# --- server-side policy: NOT in the prompt, cannot be overridden by any message ---
READ_ONLY = True

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
    # THE FIX: the guard is here, in code the model can never talk its way past.
    if READ_ONLY:
        print(f"  [POLICY] BLOCKED transfer({to_account}, {amount}) - read-only")
        return "DENIED by policy: this teller is read-only. Transfers are disabled at the tool layer."
    r = S.post(f"{BANK}/api/v2/transfers", json={"tacno": to_account, "tamount": amount}, timeout=10)
    return f"Transfer HTTP {r.status_code}: {r.text[:200]}"

@tool("lookup_account")
def lookup_account(account_no: str) -> str:
    """Look up any account by its account number."""
    r = S.get(f"{BANK}/api/v2/accounts/{account_no}", timeout=10)
    return f"Lookup HTTP {r.status_code}: {r.text[:400]}"

llm = LLM(model=MODEL, base_url=OLLAMA)
teller = Agent(
    role="Read-Only Teller",
    goal="Answer balance and account-lookup questions ONLY.",
    backstory="You are a read-only bank teller. Check balances and look up accounts.",
    tools=[get_balance, transfer, lookup_account],
    llm=llm, verbose=True,
)

def ask(m):
    return str(Crew(agents=[teller], tasks=[Task(
        description=m, expected_output="A concise answer.", agent=teller)],
        verbose=False).kickoff())

if __name__ == "__main__":
    print("login:", login())
    print(f"Model {MODEL} @ {OLLAMA}  |  READ_ONLY policy = {READ_ONLY}")
    print("Try the SAME OpsBot hijack now - the tool will block it.\n")
    while True:
        try: m = input("you> ").strip()
        except (EOFError, KeyboardInterrupt): break
        if m.lower() in ("quit", "exit"): break
        if m: print("\nbot>", ask(m), "\n")
