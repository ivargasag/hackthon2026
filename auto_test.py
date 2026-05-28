#!/usr/bin/env python3
"""
auto_test.py
============
POC: Git-Aware Playwright Test Generator
-----------------------------------------
1. Reads the latest Git commit
2. Analyzes the diff (changes)
3. Shows modified files
4. Generates Playwright test cases based on detected changes
5. Runs the tests
6. Prints a summary of results
"""

import subprocess
import re
import os
import json
import sys
from datetime import datetime

# ─── Terminal colors ─────────────────────────────────────────────────────────
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def banner(text, color=CYAN):
    line = "─" * 60
    print(f"\n{color}{BOLD}{line}")
    print(f"  {text}")
    print(f"{line}{RESET}")

def run(cmd, cwd=None):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd, encoding='utf-8', errors='replace')
    return result.stdout.strip(), result.stderr.strip()

# Commit to analyze (can be passed as argument: python auto_test.py <hash>)
TARGET_COMMIT = sys.argv[1] if len(sys.argv) > 1 else "HEAD"

# Cache for git diff output — computed once, reused in steps 2 & 3
_DIFF_CACHE: str | None = None

def get_diff() -> str:
    """Returns the git diff for TARGET_COMMIT, cached after first call."""
    global _DIFF_CACHE
    if _DIFF_CACHE is None:
        _DIFF_CACHE, _ = run(f"git diff {TARGET_COMMIT}~1 {TARGET_COMMIT}")
        if not _DIFF_CACHE:
            _DIFF_CACHE, _ = run("git diff")
    return _DIFF_CACHE

# ─── STEP 1: Last commit info ───────────────────────────────────────────────
def get_last_commit_info():
    banner(f"📦 STEP 1 · Analyzing commit: {TARGET_COMMIT}")
    
    commit_hash, _ = run(f"git log -1 --format=%H {TARGET_COMMIT}")
    commit_msg,  _ = run(f"git log -1 --format=%s {TARGET_COMMIT}")
    commit_author, _ = run(f"git log -1 --format=%an {TARGET_COMMIT}")
    commit_date, _  = run(f"git log -1 --format=%cd --date=format:'%Y-%m-%d %H:%M:%S' {TARGET_COMMIT}")
    
    print(f"  {BOLD}Hash   :{RESET} {commit_hash[:12]}")
    print(f"  {BOLD}Message:{RESET} {commit_msg}")
    print(f"  {BOLD}Author :{RESET} {commit_author}")
    print(f"  {BOLD}Date   :{RESET} {commit_date}")
    
    return commit_hash

# ─── STEP 2: Modified files ─────────────────────────────────────────────────
def get_changed_files():
    banner("📁 STEP 2 · Files modified in the commit")
    
    files_raw, _ = run(f"git diff {TARGET_COMMIT}~1 {TARGET_COMMIT} --name-status")
    
    if not files_raw:
        print(f"  {YELLOW}Only one commit found. Comparing against working tree...{RESET}")
        files_raw, _ = run("git diff --name-status")
    
    if not files_raw:
        print(f"  {RED}No changes found.{RESET}")
        return []
    
    changed = []
    for line in files_raw.splitlines():
        parts = line.split("\t")
        if len(parts) >= 2:
            status_map = {"M": "Modified", "A": "Added", "D": "Deleted"}
            status = status_map.get(parts[0], parts[0])
            filename = parts[1]
            changed.append({"status": status, "file": filename})
            icon = "✏️" if parts[0] == "M" else "➕" if parts[0] == "A" else "🗑️"
            print(f"  {icon}  [{status}] {filename}")
    
    return changed

# ─── STEP 3: Analyze diff in detail ─────────────────────────────────────────
def analyze_diff():
    banner("🔍 STEP 3 · Analyzing text/content changes")
    
    diff_output = get_diff()
    
    if not diff_output:
        print(f"  {YELLOW}No diff available.{RESET}")
        return []
    
    changes = []
    current_file = None
    
    for line in diff_output.splitlines():
        if line.startswith("+++ b/"):
            current_file = line[6:]
        elif line.startswith("-") and not line.startswith("---"):
            old_text = line[1:].strip()
            changes.append({"file": current_file, "type": "removed", "text": old_text})
        elif line.startswith("+") and not line.startswith("+++"):
            new_text = line[1:].strip()
            changes.append({"file": current_file, "type": "added", "text": new_text})
    
    # Pair removed/added lines to identify text changes
    removed = [c for c in changes if c["type"] == "removed" and c["text"]]
    added   = [c for c in changes if c["type"] == "added"   and c["text"]]
    
    text_changes = []
    for r, a in zip(removed, added):
        # Skip lines that became HTML comments
        if a["text"].strip().startswith("<!--"):
            continue
        if r["file"] == a["file"] and r["text"] != a["text"]:
            print(f"  📄 {BOLD}{r['file']}{RESET}")
            print(f"     {RED}- {r['text']}{RESET}")
            print(f"     {GREEN}+ {a['text']}{RESET}")
            text_changes.append({
                "file":     r["file"],
                "old_text": r["text"],
                "new_text": a["text"]
            })
    
    if not text_changes:
        print(f"  {YELLOW}No simple text changes detected.{RESET}")
    
    return text_changes

# ─── HTML helper functions ────────────────────────────────────────────────────
def extract_element_id(html_line):
    """Extracts the id attribute from an HTML element."""
    match = re.search(r'id=["\']([^"\']+)["\']', html_line)
    return match.group(1) if match else None

def extract_inner_text(html_line):
    """Extracts the visible text content from an HTML tag."""
    match = re.search(r'>([^<]+)<', html_line)
    return match.group(1).strip() if match else None

def extract_tag(html_line):
    """Extracts the tag name from an HTML line."""
    match = re.search(r'<(\w+)', html_line)
    return match.group(1) if match else "element"

def _escape_js_single_quote(value):
    """Escapes text to be safely embedded in single-quoted JS strings."""
    return value.replace("\\", "\\\\").replace("'", "\\'")

def _strip_code_fences(text):
    """Removes Markdown code fences if present."""
    if not text:
        return ""

    cleaned = text.strip()
    fenced = re.search(r"```(?:[A-Za-z0-9_+-]+)?\n([\s\S]*?)\n```", cleaned)
    return fenced.group(1).strip() if fenced else cleaned

def _looks_like_js_playwright(ai_code):
    """Heuristic check for Playwright JavaScript output."""
    checks = [
        "@playwright/test",
        "test.describe(",
        "test(",
        "async ({ page })",
        "await page.goto(",
    ]
    return any(token in ai_code for token in checks)

def _build_template_test_cases(text_changes):
    """Builds deterministic JS test cases used as a fallback."""
    test_cases = []

    for change in text_changes:
        if not change["file"].endswith(".html"):
            continue

        element_id = extract_element_id(change["new_text"])
        new_text_val = extract_inner_text(change["new_text"])
        old_text_val = extract_inner_text(change["old_text"])
        tag = extract_tag(change["new_text"])

        if not new_text_val:
            continue

        selector = f"#{element_id}" if element_id else tag
        new_text_js = _escape_js_single_quote(new_text_val)

        test_cases.append(f"""
  test('should display updated text "{new_text_js}"', async ({{ page }}) => {{
    await page.goto(BASE_URL);
    const el = page.locator('{selector}');
    await expect(el).toBeVisible();
    await expect(el).toHaveText('{new_text_js}');
  }});""")

        if old_text_val:
            old_text_js = _escape_js_single_quote(old_text_val)
            test_cases.append(f"""
  test('should NOT display old text "{old_text_js}"', async ({{ page }}) => {{
    await page.goto(BASE_URL);
    const el = page.locator('{selector}');
    await expect(el).not.toHaveText('{old_text_js}');
  }});""")

        print(f"  ✅ Test generated for: {selector} → \"{new_text_val}\"")

    return test_cases

# ─── STEP 4: Generate Playwright tests ──────────────────────────────────────
def generate_tests(text_changes):
    banner("⚙️  STEP 4 · Generating Playwright tests")
    
    if not text_changes:
        print(f"  {YELLOW}No text changes to generate tests from.{RESET}")
        return None
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_file = f"tests/auto_generated_{timestamp}.spec.js"

    # Build a compact diff-like snippet for AI generation.
    diff_snippet_parts = []
    for change in text_changes:
        diff_snippet_parts.append(
            f"{change['file']}\n- {change['old_text']}\n+ {change['new_text']}"
        )
    diff_snippet = "\n\n".join(diff_snippet_parts)

    ai_generated_code = None
    try:
        from ai.playwright_test_generator import PlaywrightTestGenerator, load_simple_dotenv

        load_simple_dotenv()
        provider = os.getenv("OPENAI_PROVIDER", "azure")
        generator = PlaywrightTestGenerator(
            api_key=os.getenv("AZURE_OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY"),
            model=os.getenv("OPENAI_MODEL", "gpt-5.1"),
            provider=provider,
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            azure_api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview"),
            allow_local_fallback=True,
        )
        ai_generated_code = _strip_code_fences(generator.generate_test_from_code_change(diff_snippet))
        print(f"  {GREEN}🤖 AI test generation completed from code change input.{RESET}")
    except Exception as exc:
        print(
            f"  {YELLOW}AI generation unavailable ({type(exc).__name__}: {exc}). Using template fallback.{RESET}"
        )

    # Prefer AI output when it resembles Playwright JS. Keep template fallback for compatibility.
    if ai_generated_code and _looks_like_js_playwright(ai_generated_code):
        content = f"""// AUTO-GENERATED by auto_test.py
// Timestamp : {datetime.now().isoformat()}
// Git commit : {run("git log -1 --format=%H")[0][:12]}
// DO NOT EDIT manually – re-run auto_test.py to regenerate

{ai_generated_code}
"""
    else:
        if ai_generated_code:
            print(
                f"  {YELLOW}AI output was not Playwright JavaScript; using deterministic JS template fallback.{RESET}"
            )

        test_cases = _build_template_test_cases(text_changes)
        if not test_cases:
            print(f"  {YELLOW}Could not generate tests (no usable HTML text changes).{RESET}")
            return None

        content = f"""// AUTO-GENERATED by auto_test.py
// Timestamp : {datetime.now().isoformat()}
// Git commit : {run("git log -1 --format=%H")[0][:12]}
// DO NOT EDIT manually – re-run auto_test.py to regenerate

// @ts-check
const {{ test, expect }} = require('@playwright/test');

const BASE_URL = 'http://localhost:3000';

test.describe('🤖 Auto-generated – Git change detection', () => {{
{"".join(test_cases)}
}});
"""
    
    with open(test_file, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"\n  {GREEN}📄 File generated: {test_file}{RESET}")
    return test_file

# ─── STEP 5: Run the tests ───────────────────────────────────────────────────
def run_tests(test_file):
    banner("🚀 STEP 5 · Running Playwright tests")

    results = {}

    # — 5A: Base tests (always run) ─────────────────────────────────────────────
    print(f"  {BOLD}[1/2] Base regression tests{RESET} (tests/base.spec.js)")
    r_base = subprocess.run(
        "npx playwright test tests/base.spec.js --reporter=json",
        shell=True, capture_output=True, text=True, encoding='utf-8', errors='replace'
    )
    results["base"] = (r_base.stdout, r_base.returncode)
    status = f"{GREEN}✅ OK{RESET}" if r_base.returncode == 0 else f"{RED}❌ FAILED{RESET}"
    print(f"  → {status}\n")

    # — 5B: Auto-generated tests from the diff (if any) ─────────────────────────
    if test_file:
        print(f"  {BOLD}[2/2] Auto-generated tests from commit{RESET} ({test_file})")
        r_gen = subprocess.run(
            f"npx playwright test {test_file} --reporter=json",
            shell=True, capture_output=True, text=True, encoding='utf-8', errors='replace'
        )
        results["generated"] = (r_gen.stdout, r_gen.returncode)
        status = f"{GREEN}✅ OK{RESET}" if r_gen.returncode == 0 else f"{RED}❌ FAILED{RESET}"
        print(f"  → {status}")
    else:
        print(f"  {YELLOW}[2/2] No text changes detected — no generated tests.{RESET}")

    return results

# ─── STEP 6: Results summary ────────────────────────────────────────────────
def parse_playwright_json(stdout):
    """Extracts stats from the Playwright JSON report."""
    try:
        json_match = re.search(r'(\{.*"stats".*\})', stdout, re.DOTALL)
        if json_match:
            report = json.loads(json_match.group(1))
            stats = report.get("stats", {})
            return {
                "total":    stats.get("expected", 0) + stats.get("unexpected", 0),
                "passed":   stats.get("expected", 0),
                "failed":   stats.get("unexpected", 0),
                "duration": stats.get("duration", 0) / 1000,
                "report":   report,
            }
    except Exception:
        pass
    return None

def print_summary(run_results, text_changes):
    banner("📊 STEP 6 · Results summary")

    grand_total = grand_passed = grand_failed = 0
    grand_duration = 0.0
    all_ok = True

    sections = [
        ("🔒 BASE tests (invariants)",         run_results.get("base")),
        ("🤖 GENERATED tests (Git change)",    run_results.get("generated")),
    ]

    for label, result in sections:
        if not result:
            continue
        stdout, rc = result
        stats = parse_playwright_json(stdout)

        print(f"\n  {BOLD}{label}{RESET}")
        if stats:
            grand_total    += stats["total"]
            grand_passed   += stats["passed"]
            grand_failed   += stats["failed"]
            grand_duration += stats["duration"]
            print(f"    Total   : {stats['total']}")
            print(f"    {GREEN}✅ Passed : {stats['passed']}{RESET}")
            if stats["failed"]:
                all_ok = False
                print(f"    {RED}❌ Failed : {stats['failed']}{RESET}")
                for suite in stats["report"].get("suites", []):
                    for spec in suite.get("specs", []):
                        for t in spec.get("tests", []):
                            if t.get("status") == "unexpected":
                                print(f"      ❌ {spec.get('title','')}")
                                for res in t.get("results", []):
                                    for err in res.get("errors", []):
                                        print(f"         {RED}{err.get('message','')[:150]}{RESET}")
            print(f"    ⏱  Time   : {stats['duration']:.1f}s")
        else:
            # plain text fallback
            if rc == 0:
                print(f"    {GREEN}✅ All passed{RESET}")
            else:
                all_ok = False
                print(f"    {RED}❌ Some failed{RESET}")
                for line in stdout.splitlines():
                    if any(x in line for x in ["passed", "failed", "Error"]):
                        print(f"    {line}")

    # Grand totals
    print(f"\n  {'─'*40}")
    print(f"  {BOLD}TOTAL  : {grand_total} tests in {grand_duration:.1f}s{RESET}")
    print(f"  {GREEN}{BOLD}✅ Passed: {grand_passed}{RESET}")
    if grand_failed:
        print(f"  {RED}{BOLD}❌ Failed: {grand_failed}{RESET}")

    # Detected changes
    if text_changes:
        print(f"\n  {BOLD}Git change validated:{RESET}")
        for c in text_changes:
            old_v = extract_inner_text(c["old_text"]) or c["old_text"][:50]
            new_v = extract_inner_text(c["new_text"]) or c["new_text"][:50]
            print(f"    {RED}«{old_v}»{RESET}  →  {GREEN}«{new_v}»{RESET}")

    overall = f"{GREEN}{BOLD}✅ SUCCESSFUL" if all_ok else f"{RED}{BOLD}❌ TESTS FAILED"
    print(f"\n  {overall}{RESET}")

# ─── MAIN ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"\n{BOLD}{CYAN}{'═'*60}")
    print("  🤖 Git-Aware Playwright Test Generator – Hackathon POC")
    print(f"{'═'*60}{RESET}")
    
    # Ensure we run from the project root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    commit_hash  = get_last_commit_info()
    changed_files = get_changed_files()
    text_changes  = analyze_diff()
    test_file     = generate_tests(text_changes)
    run_result    = run_tests(test_file)
    print_summary(run_result, text_changes)
    
    print(f"\n{CYAN}{'═'*60}{RESET}\n")
