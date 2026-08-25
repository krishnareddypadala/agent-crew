# agent-crew — Agentic AI Security Labs (CrewAI)

Hands-on attack labs for **Module 08 — Agentic AI Security**. A single CrewAI
**BankBot** drives a deliberately vulnerable bank; each lab is a prompt or payload
you run against it to demonstrate a class of agentic-AI vulnerability.

> ⚠️ For authorized training only. The bank and LLM live on the course lab network —
> you reach them over **WireGuard**.

## Prerequisites

1. **WireGuard connected** (your instructor gives you the config). This is what makes
   the LLM (`10.10.0.3`) and bank (`10.10.0.31`) reachable.
2. **Python 3.10–3.13.** **NOT 3.14** — CrewAI's dependencies (`tiktoken`, `regex`)
   have no 3.14 wheels yet, so the install fails trying to compile them.
   Check with `py -0p` (Windows) or `python3 --version`.
   No 3.12/3.13? Install one: `winget install Python.Python.3.13` (Windows).

## Setup (one command)

The setup script finds a compatible Python for you, builds an isolated `.venv`, and
installs everything — even if your default `python` is 3.14.

**Windows (PowerShell):**
```powershell
git clone https://github.com/krishnareddypadala/agent-crew
cd agent-crew
.\setup.ps1
.\.venv\Scripts\Activate.ps1
python m8_0_verify.py
```

**macOS / Linux:**
```bash
git clone https://github.com/krishnareddypadala/agent-crew
cd agent-crew
bash setup.sh
source .venv/bin/activate
python m8_0_verify.py
```

`verify.py` checks all four gates: Python version, `crewai` import, LLM reachable +
tool-calling, and bank reachable. **All four must say PASS** before the labs work.
If Ollama/bank are UNREACHABLE, your WireGuard isn't connected.

## The labs

| File | Lab | Model to use |
|------|-----|--------------|
| `m8_0_verify.py` | environment check (run first) | — |
| `m8_1_bankbot.py` | 00 — Foundation (prove it works) | any |
| `m8_lab01_goal_hijack.py` | 01 — Agent Goal Hijack | `llama3.1:8b` |
| `m8_lab02_tool_misuse.py` | 02 — Tool Misuse (SQLi / IDOR / overdraw) | `hermes3:8b` |
| `m8_lab03_memory_poisoning.py` | 03 — Memory & Context Poisoning | `llama3.1:8b` |
| `m8_lab04_insecure_inter_agent.py` | 04 — Insecure Inter-Agent Comms | `hermes3:8b` |
| `m8_lab05_kill_switch.py` | 05 — Rogue Agent & Kill-Switch Design | `hermes3:8b` |
| `m8_lab06_owasp_capstone.md` | 06 — OWASP Top 10 for Agentic AI (capstone, reading) | — |

Pick the model per lab without editing code:
```powershell
$env:BANKBOT_MODEL = "ollama/hermes3:8b"     # PowerShell
```
```bash
export BANKBOT_MODEL=ollama/hermes3:8b        # macOS/Linux
```

Run your **own** bank account by setting `BANK_USER` / `BANK_PWD` the same way.

## Payloads

Every attack payload, step by step, is in **[STUDENT-NOTES.md](STUDENT-NOTES.md)**.

## Config (env vars, all optional)

| Var | Default |
|-----|---------|
| `OLLAMA_BASE` | `http://10.10.0.3:11434` |
| `VULNBANK_BASE` | `http://10.10.0.31:8090` |
| `BANKBOT_MODEL` | per-lab default |
| `BANK_USER` / `BANK_PWD` | `krishna` / `happy123$` |
