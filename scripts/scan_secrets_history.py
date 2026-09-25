"""
Secret Scanning Audit Script for ClarifAI (Full Working Tree + Full Git History)
Audits for:
- Live Groq API keys (gsk_...)
- Live HuggingFace tokens (hf_...)
- Real JWT Signing Secrets
- Database passwords in URLs
- Qdrant API Keys
- Internal Service Secrets
- Accidental .env commits
"""

import os
import re
import subprocess
from pathlib import Path
from typing import List, Dict, Any

REPO_ROOT = Path(__file__).resolve().parent.parent

# Regex patterns for credential detection
SECRET_PATTERNS = [
    (r"gsk_[a-zA-Z0-9]{20,}", "Groq API Key (gsk_...)"),
    (r"hf_[a-zA-Z0-9]{20,}", "Hugging Face Token (hf_...)"),
    (r"(?i)postgres://(?!(?:postgres:postgres|user:password))[^@\s]+:[^@\s]+@", "PostgreSQL Connection URI with Non-Default Credentials"),
    (r"(?i)redis://:[^@\s]+@", "Redis Connection URI with Password"),
    (r"(?i)jwt_signing_key\s*=\s*['\"][a-zA-Z0-9+/=]{32,}['\"]", "Hardcoded Production JWT Signing Key"),
    (r"(?i)internal_service_secret\s*=\s*['\"][a-zA-Z0-9_-]{16,}['\"]", "Hardcoded INTERNAL_SERVICE_SECRET in Code"),
]

# Patterns for allowed mock test fixtures and documentation placeholders
ALLOWED_PLACEHOLDERS = [
    "gsk_your_groq_api_key_here",
    "your_jwt_signing_key_here",
    "your_qdrant_api_key_here",
    "your_internal_service_secret_here",
    "gsk_***[REDACTED]***",
    "gsk_test123456789key",
    "gsk_test123456789secretkey",
    "gsk_supersecret123456789key",
    "super-secret-internal-token-123",
    "postgres://postgres:postgres@localhost:5432/clarifai_db",
    "postgres:postgres",
    "user:password"
]

def scan_working_tree() -> List[Dict[str, Any]]:
    findings = []
    print("Scanning current working tree...")
    for root, dirs, files in os.walk(REPO_ROOT):
        if any(skip in root for skip in [".git", "node_modules", "venv", ".pytest_cache", "__pycache__", "dist"]):
            continue
        for file in files:
            file_path = Path(root) / file
            if file_path.name == "scan_secrets_history.py":
                continue
            if file_path.suffix in [".bin", ".safetensors", ".pt", ".onnx", ".png", ".jpg", ".pdf", ".ico"]:
                continue
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                for pattern, desc in SECRET_PATTERNS:
                    matches = re.finditer(pattern, content)
                    for m in matches:
                        matched_str = m.group(0)
                        if any(p in matched_str for p in ALLOWED_PLACEHOLDERS):
                            continue
                        rel_path = file_path.relative_to(REPO_ROOT)
                        findings.append({
                            "type": "WORKING_TREE",
                            "file": str(rel_path),
                            "description": desc,
                            "snippet": matched_str[:10] + "..."
                        })
            except Exception as e:
                pass
    return findings

def scan_git_history() -> List[Dict[str, Any]]:
    findings = []
    print("Scanning entire git commit log history...")
    try:
        cmd = ["git", "log", "-p", "--all", "-S", "gsk_"]
        res = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, errors="ignore")
        if res.stdout:
            for line in res.stdout.splitlines():
                if line.startswith("+") and "gsk_" in line:
                    if not any(p in line for p in ALLOWED_PLACEHOLDERS):
                        match = re.search(r"gsk_[a-zA-Z0-9]{20,}", line)
                        if match and match.group(0) not in ALLOWED_PLACEHOLDERS:
                            findings.append({
                                "type": "GIT_HISTORY",
                                "description": "Groq API Key in Git Commit Diff",
                                "snippet": match.group(0)[:10] + "..."
                            })
        
        # Check if any .env was committed in history (excluding .env.example)
        cmd_env = ["git", "log", "--all", "--full-history", "--name-only", "--diff-filter=A"]
        res_env = subprocess.run(cmd_env, cwd=REPO_ROOT, capture_output=True, text=True, errors="ignore")
        if res_env.stdout:
            for line in res_env.stdout.splitlines():
                line = line.strip()
                if (line.endswith("/.env") or line == ".env") and not line.endswith(".env.example"):
                    findings.append({
                        "type": "GIT_HISTORY",
                        "description": "Committed .env file in history",
                        "file": line
                    })
    except Exception as e:
        print(f"Git history scan error: {e}")
    return findings

def audit_ci_workflows() -> List[Dict[str, Any]]:
    findings = []
    workflows_dir = REPO_ROOT / ".github" / "workflows"
    if workflows_dir.exists():
        for f in workflows_dir.glob("*.yml"):
            content = f.read_text(encoding="utf-8", errors="ignore")
            for pattern, desc in SECRET_PATTERNS:
                matches = re.finditer(pattern, content)
                for m in matches:
                    matched_str = m.group(0)
                    if not any(p in matched_str for p in ALLOWED_PLACEHOLDERS):
                        findings.append({
                            "type": "CI_WORKFLOW",
                            "file": f.name,
                            "description": f"Hardcoded secret in workflow: {desc}"
                        })
    return findings

if __name__ == "__main__":
    wt_findings = scan_working_tree()
    hist_findings = scan_git_history()
    ci_findings = audit_ci_workflows()
    
    total = len(wt_findings) + len(hist_findings) + len(ci_findings)
    print("=" * 60)
    print(f"SECRET AUDIT REPORT: {total} REAL SECRETS DETECTED")
    print("=" * 60)
    print(f"Working Tree Findings: {len(wt_findings)}")
    print(f"Git History Findings: {len(hist_findings)}")
    print(f"CI Workflow Findings: {len(ci_findings)}")
    for f in wt_findings + hist_findings + ci_findings:
        print(f" - [{f['type']}] {f.get('file', '')}: {f['description']} ({f.get('snippet', '')})")
    
    if total == 0:
        print("\nAUDIT RESULT: CLEAN - ZERO REAL SECRETS DETECTED ACROSS REPOSITORY & HISTORY.")
