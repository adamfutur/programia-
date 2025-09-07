# agent.py
import os
import subprocess
import json
import re
from pathlib import Path
from typing import Dict, Any, List
from openai import OpenAI
from langgraph.graph import StateGraph, END

# -----------------------
# Config
# -----------------------
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
)

MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
PROJECTS_DIR = Path("projects")
MAX_ITERATIONS = int(os.getenv("MAX_AGENT_ITERS", 5))

# -----------------------
# Utilities
# -----------------------
def detect_language(project: Path) -> str:
    if (project / "package.json").exists():
        return "node"
    elif (project / "pom.xml").exists():
        return "java"
    elif any(project.glob("*.py")) or (project / "requirements.txt").exists():
        return "python"
    else:
        return "unknown"

def run_tests(project: Path) -> str:
    lang = detect_language(project)
    try:
        if lang == "python":
            proc = subprocess.run(["pytest", "-q"], cwd=project, capture_output=True, text=True, timeout=60)
        elif lang == "node":
            proc = subprocess.run(["npm", "test"], cwd=project, capture_output=True, text=True, timeout=60)
        elif lang == "java":
            proc = subprocess.run(["mvn", "test"], cwd=project, capture_output=True, text=True, timeout=120)
        else:
            return "⚠️ Unknown language, cannot run tests."
        return proc.stdout + proc.stderr
    except subprocess.TimeoutExpired:
        return "⏳ Tests timed out."

def get_source_files(project: Path) -> List[Path]:
    lang = detect_language(project)
    if lang == "python":
        return list(project.rglob("*.py"))
    elif lang == "node":
        return list(project.rglob("*.js"))
    elif lang == "java":
        return list(project.rglob("*.java"))
    else:
        return []

def ask_llm(prompt: str) -> str:
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    return resp.choices[0].message.content.strip()

def safe_get(state: Dict[str, Any], key: str, default=None):
    return state[key] if key in state else default

def parse_llm_json(output: str) -> list:
    try:
        m = re.search(r"```(?:json)?\s*(\{.*\})\s*```", output, re.DOTALL)
        json_str = m.group(1) if m else output.strip()
        data = json.loads(json_str)
        return data.get("files", [])
    except Exception as e:
        print(f"⚠️ Failed to parse JSON: {e}")
        print("LLM output:\n", output[:500])
        return []

def apply_fixes(project: Path, files: List[Dict[str, str]]):
    for file in files:
        rel_path = file.get("path")
        content = file.get("content", "")
        if not rel_path or not content:
            continue
        target = project / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            backup = target.with_suffix(target.suffix + ".bak")
            target.rename(backup)
        target.write_text(content, encoding="utf-8")
        print(f"✅ Updated {target}")

def get_failed_files(test_output: str) -> List[str]:
    failed = []
    for line in test_output.splitlines():
        if line.startswith("FAILED") and "::" in line:
            failed.append(line.split("::")[0].strip())
    return list(set(failed))

# -----------------------
# Graph Nodes
# -----------------------
def node_understand(state: Dict[str, Any]) -> Dict[str, Any]:
    project = safe_get(state, "project")
    if not project:
        state["requirements"] = "⚠️ No project path found."
        return state
    readme_path = project / "README.md"
    readme = readme_path.read_text() if readme_path.exists() else "(no README.md)"
    test_output = run_tests(project)
    lang = detect_language(project)
    prompt = f"""You are an assistant for a {lang} project. Analyze this project.

README:
{readme}

Current test output:
{test_output}

Give a concise list of requirements and what seems broken.
"""
    state["requirements"] = ask_llm(prompt)
    return state

def node_plan(state: Dict[str, Any]) -> Dict[str, Any]:
    reqs = safe_get(state, "requirements", "")
    prompt = f"""Requirements:
{reqs}

Create a step-by-step coding plan:
- Files to change
- Functions to implement
- Fixes required
"""
    state["plan"] = ask_llm(prompt)
    return state

def node_code(state: Dict[str, Any]) -> Dict[str, Any]:
    plan = safe_get(state, "plan", "")
    project = safe_get(state, "project")
    lang = detect_language(project)
    files_list = get_source_files(project)
    file_contents = "\n".join(f"=== {f.relative_to(project)} ===\n{f.read_text()[:1000]}" for f in files_list)
    prompt = f"""You are coding assistant for a {lang} project.

Plan:
{plan}

Current project files:
{file_contents}

Generate corrected code snippets or full file replacements in JSON:
{{
  "files": [
    {{"path": "relative/path/to/file", "content": "new content"}}
  ]
}}
"""
    code_output = ask_llm(prompt)
    state["code"] = code_output
    files = parse_llm_json(code_output)
    if project:
        apply_fixes(project, files)
    return state

def node_identify_errors(state: Dict[str, Any]) -> Dict[str, Any]:
    project = safe_get(state, "project")
    test_output = run_tests(project)
    state["test_output"] = test_output
    failed_files = get_failed_files(test_output)
    lang = detect_language(project)
    prompt = f"""You are an assistant for a {lang} project.

Test results:
{test_output}

Failed files:
{', '.join(failed_files) if failed_files else 'None'}

Explain what is failing and why.
"""
    state["error_analysis"] = ask_llm(prompt)
    return state

def node_fix(state: Dict[str, Any]) -> Dict[str, Any]:
    project = safe_get(state, "project")
    errors = safe_get(state, "error_analysis", "")
    previous_fix = safe_get(state, "fix", "")
    lang = detect_language(project)
    files_list = get_source_files(project)
    file_contents = "\n".join(f"=== {f.relative_to(project)} ===\n{f.read_text()[:1000]}" for f in files_list)
    prompt = f"""Previous fix attempt:
{previous_fix}

Errors found:
{errors}

Current project files:
{file_contents}

Generate corrected file contents in JSON. Include only files that need changes.
"""
    fix_output = ask_llm(prompt)
    state["fix"] = fix_output
    files = parse_llm_json(fix_output)
    if project:
        apply_fixes(project, files)
    return state

def node_validate(state: Dict[str, Any]) -> Dict[str, Any]:
    project = safe_get(state, "project")
    test_output = run_tests(project)
    state["tests_passed"] = "failed" not in test_output.lower()
    lang = detect_language(project)
    prompt = f"""Final test results for a {lang} project:

{test_output}

Summarize: Did all tests pass? If not, what remains?
"""
    state["validation"] = ask_llm(prompt)
    return state

# -----------------------
# Judge Standout Summary
# -----------------------
def node_judge_summary(state: Dict[str, Any]) -> Dict[str, Any]:
    project = safe_get(state, "project")
    tests_passed = safe_get(state, "tests_passed", False)
    plan = safe_get(state, "plan", "")
    code_changes = safe_get(state, "code", "")
    fix_changes = safe_get(state, "fix", "")
    lang = detect_language(project)
    prompt = f"""
You are a hackathon judge assistant.

Project: {project.name}
Language: {lang}
Tests passed: {tests_passed}

Plan executed:
{plan}

Code changes made:
{code_changes}

Fixes applied:
{fix_changes}

Write a concise, impressive summary for judges highlighting:
1. What the project does
2. How the agent improved/fixed it
3. Why it is now better and unique
4. Make it engaging and standout
"""
    summary = ask_llm(prompt)
    state["judge_summary"] = summary

    print("\n=== Judge Standout Summary ===")
    print(summary)
    print("============================\n")
    return state

# -----------------------
# Graph Definition
# -----------------------
def build_graph():
    g = StateGraph(dict)
    g.add_node("understand", node_understand)
    g.add_node("plan", node_plan)
    g.add_node("code", node_code)
    g.add_node("identify", node_identify_errors)
    g.add_node("fix", node_fix)
    g.add_node("validate", node_validate)
    g.add_node("judge_summary", node_judge_summary)

    g.set_entry_point("understand")
    g.add_edge("understand", "plan")
    g.add_edge("plan", "code")
    g.add_edge("code", "identify")
    g.add_edge("identify", "fix")
    g.add_edge("fix", "validate")
    g.add_edge("validate", "judge_summary")
    g.add_edge("judge_summary", END)
    return g.compile()

# -----------------------
# Main
# -----------------------
def main():
    print("=== Mini Coding Agent ===")
    projects = [p for p in PROJECTS_DIR.iterdir() if p.is_dir()]
    graph = build_graph()
    for project in projects:
        print(f"\n🚀 Processing {project.name}...\n")
        iteration = 0
        final_state = {"project": project}
        while iteration < MAX_ITERATIONS:
            print(f"--- Iteration {iteration + 1} ---")
            final_state = graph.invoke(final_state)
            if safe_get(final_state, "tests_passed", False):
                print(f"🎉 All tests passed for {project.name}!")
                break
            else:
                print(f"❌ Tests still failing for {project.name}. Iterating again...")
                iteration += 1
        print("\n--- REPORT ---")
        print("Requirements:\n", final_state.get("requirements", ""))
        print("\nPlan:\n", final_state.get("plan", ""))
        print("\nCode Proposal:\n", final_state.get("code", ""))
        print("\nError Analysis:\n", final_state.get("error_analysis", ""))
        print("\nFix Proposal:\n", final_state.get("fix", ""))
        print("\nValidation:\n", final_state.get("validation", ""))
        print("\nJudge Standout Summary:\n", final_state.get("judge_summary", ""))

if __name__ == "__main__":
    main()
