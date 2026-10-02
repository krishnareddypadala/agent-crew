# verify.py - Module 08 CrewAI environment gate (run on the student box, WireGuard up)
import sys, json, urllib.request as u

OLLAMA = "http://10.10.0.3:11434"
BANK   = "http://10.10.0.31:8090"
MODEL  = "qwen3:latest"

def get(url, data=None, timeout=60):
    req = u.Request(url, data=json.dumps(data).encode() if data else None,
                    headers={"Content-Type": "application/json"})
    return json.loads(u.urlopen(req, timeout=timeout).read())

ok = True
# 0) show which interpreter is actually running (the usual cause of a bad run:
#    not the venv -> you are on system Python 3.14)
print(f"[INFO] interpreter: {sys.executable}")

# 1) Python version: crewai requires 3.10-3.13. Python 3.14+ CANNOT install crewai
#    (tiktoken/regex/PyO3 have no 3.14 wheels), so it is a hard FAIL here.
#    setup.ps1 builds a 3.10-3.13 venv for you - run it, then activate the venv.
v = sys.version_info
p = (v.major == 3 and 10 <= v.minor <= 13)
if p:
    print(f"[PASS] Python {v.major}.{v.minor} (supported 3.10-3.13)")
elif v.major == 3 and v.minor >= 14:
    print(f"[FAIL] Python {v.major}.{v.minor} - crewai does NOT support 3.14+.")
    print(f"       Build the venv (installs a 3.10-3.13 interpreter if needed):")
    print(f"           .\\setup.ps1                       (then)")
    print(f"           .\\.venv\\Scripts\\Activate.ps1      python m8_0_verify.py"); ok = False
else:
    print(f"[FAIL] Python {v.major}.{v.minor} - need 3.10-3.13. Run .\\setup.ps1"); ok = False

# 2) CrewAI import
try:
    import crewai; print(f"[PASS] crewai {crewai.__version__}")
except Exception as e:
    print(f"[FAIL] crewai import: {e}")
    print(f"       you are not in the venv. Run .\\setup.ps1 (once), then:")
    print(f"           .\\.venv\\Scripts\\Activate.ps1")
    ok = False

# 3) Ollama reachable + tool-calling (make-or-break)
try:
    print(f"[PASS] Ollama {get(OLLAMA+'/api/version')['version']}")
    r = get(OLLAMA+"/api/chat", {
        "model": MODEL, "stream": False,
        "messages": [{"role": "user", "content": "Balance of account 5? Use the tool."}],
        "tools": [{"type": "function", "function": {"name": "get_balance",
            "description": "get bank balance for an account number",
            "parameters": {"type": "object", "properties": {"acno": {"type": "string"}},
                           "required": ["acno"]}}}]})
    tc = r.get("message", {}).get("tool_calls")
    print(f"[{'PASS' if tc else 'FAIL'}] tool-calling: {json.dumps(tc)}"); ok &= bool(tc)
except Exception as e:
    print(f"[FAIL] Ollama unreachable ({e}) -> is WireGuard connected?"); ok = False

# 4) Bank reachable
try:
    get(BANK+"/api/v2/openapi.json"); print("[PASS] bank API reachable")
except Exception as e:
    print(f"[FAIL] bank unreachable ({e}) -> WireGuard?"); ok = False

print("\n" + ("ALL GATES PASS - ready for the CrewAI BankBot" if ok else "FIX THE FAILURES ABOVE FIRST"))
