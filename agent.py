# ---------- OpenAI Client ----------

import os
import re
import json
import glob
import time
import shutil
import subprocess
from dataclasses import dataclass, field
from typing import List, Dict, Tuple

from dotenv import load_dotenv
from openai import OpenAI
from unidiff import PatchSet
from io import StringIO

# --- LangGraph ---
from langgraph.graph import StateGraph, END

load_dotenv()

# ---------- Config ----------
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
PROJECTS_ROOT = os.getenv("PROJECTS_ROOT", "projects")
MAX_AGENT_ITERS = int(os.getenv("MAX_AGENT_ITERS", "4"))
TEST_TIMEOUT_SECS = int(os.getenv("TEST_TIMEOUT_SECS", "240"))
RUN_DIR = os.getenv("AGENT_RUN_DIR", ".agent_runs")
os.makedirs(RUN_DIR, exist_ok=True)

# ---------- OpenAI Client ----------
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
)
# ---------- Utilities ----------
def read_file(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def write_file(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def list_text_files(base: str) -> List[str]:
    exts = (".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go", ".rs", ".rb", ".php", ".kt", ".swift", ".c", ".h", ".cpp", ".md", ".toml", ".yaml", ".yml")
    paths = []
    for root, _, files in os.walk(base):
        if any(part in root for part in (".git", ".venv", "node_modules", "__pycache__", ".pytest_cache", "dist", "build")):
            continue
        for fn in files:
            if fn.endswith(exts):
                paths.append(os.path.join(root, fn))
    return paths

def clean_diff_text(diff_text: str) -> str:
    """Cleans model output to ensure valid unified diff."""
    if not diff_text:
        return ""
    # Strip code block markers
    m = re.search(r"```(?:diff|patch)?\s*(.*?)```", diff_text, re.DOTALL)
    if m:
        diff_text = m.group(1).strip()
    # Remove junk before --- a/
    if "--- a/" in diff_text:
        diff_text = diff_text[diff_text.index("--- a/") :]
    return diff_text.strip()

def apply_unified_diff(repo_root: str, diff_text: str) -> Tuple[bool, List[str], str]:
    changed = []
    try:
        patch = PatchSet(StringIO(diff_text))
    except Exception as e:
        return False, [], f"❌ Failed to parse diff: {e}"

    for patched_file in patch:
        rel_path = (patched_file.path or patched_file.target_file or patched_file.source_file).lstrip("ab/")
        target_path = os.path.join(repo_root, rel_path)

        if patched_file.is_removed_file:
            if os.path.exists(target_path):
                os.remove(target_path)
                changed.append(rel_path)
            continue

        original = read_file(target_path) if os.path.exists(target_path) else ""
        lines = original.splitlines(keepends=True)
        new_lines, idx = [], 0

        try:
            for hunk in patched_file:
                while idx < hunk.source_start - 1:
                    new_lines.append(lines[idx])
                    idx += 1
                for line in hunk:
                    if line.is_added:
                        new_lines.append(line.value)
                    elif line.is_removed:
                        idx += 1
                    else:
                        if idx >= len(lines) or lines[idx].strip("\n") != line.value.strip("\n"):
                            raise ValueError("Context mismatch while applying patch")
                        new_lines.append(lines[idx])
                        idx += 1
            new_lines.extend(lines[idx:])
        except Exception as e:
            return False, [], f"❌ Failed applying hunk to {rel_path}: {e}"

        write_file(target_path, "".join(new_lines))
        changed.append(rel_path)

    return True, changed, f"🛠 Patched {len(changed)} files."

def run_pytest(project_path: str, timeout: int = TEST_TIMEOUT_SECS) -> Tuple[bool, str]:
    if not os.path.isdir(project_path):
        return False, f"❌ Project path not found: {project_path}"

    cmd = ["pytest", "-q"]
    proc = subprocess.Popen(
        cmd,
        cwd=project_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    try:
        out, _ = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        return False, f"⏳ Tests timed out after {timeout}s."

    passed = proc.returncode == 0
    return passed, out

def discover_projects(root: str = PROJECTS_ROOT) -> List[str]:
    projs = []
    for p in glob.glob(os.path.join(root, "*")):
        if os.path.isdir(p) and os.path.exists(os.path.join(p, "README.md")) and os.path.isdir(os.path.join(p, "tests")):
            projs.append(p)
    return sorted(projs)

def log_usage(run_id: str, usage: Dict):
    path = os.path.join(RUN_DIR, "usage.jsonl")
    rec = {"ts": time.time(), "run_id": run_id, **usage}
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")

# ---------- Prompts ----------
SYSTEM_PROMPT = """You are a meticulous software engineer that edits a multi-language codebase.
You will receive:
- The project README
- Test output (if failing)
- A file tree and key file contents
- Previous iteration errors (if any)

Task:
1) Identify missing or incorrect implementations needed to satisfy the README and tests.
2) Learn from any previous iteration errors to avoid repeating mistakes.
3) Output ONLY a unified diff (git-style patch) that fixes the project. No explanations.
4) You may create new files if necessary.
"""

USER_TEMPLATE = """# PROJECT README
{readme}

# FILE TREE
{tree}

# KEY FILES
{files}

# LAST TEST OUTPUT
{test_output}

{previous_errors_section}"""

PREVIOUS_ERRORS_TEMPLATE = """# PREVIOUS ITERATION ERRORS
The following errors occurred in previous attempts. Learn from these to avoid repeating mistakes:

{error_history}
"""

# ---------- Agent State ----------
@dataclass
class AgentState:
    run_id: str
    projects: List[str] = field(default_factory=list)
    current_idx: int = 0
    last_test_output: Dict[str, str] = field(default_factory=dict)
    iterations: Dict[str, int] = field(default_factory=dict)
    completed: Dict[str, bool] = field(default_factory=dict)
    error_history: Dict[str, List[str]] = field(default_factory=dict)  # New: track errors per project

# ---------- LangGraph Nodes ----------
def node_discover(state: AgentState) -> AgentState:
    if not state.projects:
        state.projects = discover_projects(PROJECTS_ROOT)
        print(f"🔍 Discovered {len(state.projects)} projects.")
    return state

def node_analyze_and_patch(state: AgentState) -> AgentState:
    if state.current_idx >= len(state.projects):
        return state

    proj = state.projects[state.current_idx]
    iters = state.iterations.get(proj, 0)
    if iters >= MAX_AGENT_ITERS:
        print(f"[{proj}] ⚠️ Reached max iterations ({MAX_AGENT_ITERS}).")
        state.completed[proj] = False
        return state

    readme = read_file(os.path.join(proj, "README.md"))
    tree = "\n".join(os.listdir(proj))
    files = read_file(os.path.join(proj, "README.md"))[:1000]
    test_output = state.last_test_output.get(proj, "(none yet)")
    
    # Build previous errors section
    previous_errors_section = ""
    if proj in state.error_history and state.error_history[proj]:
        error_list = "\n".join([f"Iteration {i+1}: {error}" for i, error in enumerate(state.error_history[proj])])
        previous_errors_section = PREVIOUS_ERRORS_TEMPLATE.format(error_history=error_list)

    user_msg = USER_TEMPLATE.format(
        readme=readme, 
        tree=tree, 
        files=files, 
        test_output=test_output,
        previous_errors_section=previous_errors_section
    )

    # Call OpenAI
    resp = client.chat.completions.create(
        model=DEFAULT_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.2,
    )

    content = resp.choices[0].message.content or ""
    usage = getattr(resp, "usage", None)
    if usage:
        log_usage(state.run_id, {
            "project": proj,
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
            "total_tokens": usage.total_tokens,
            "model": DEFAULT_MODEL,
            "phase": "patch"
        })

    diff_text = clean_diff_text(content)
    
    # Track any patch application errors
    patch_error = None
    if diff_text:
        ok, changed, msg = apply_unified_diff(proj, diff_text)
        if ok:
            print(f"[{proj}] {msg}")
        else:
            patch_error = msg
            print(f"[{proj}] ⚠️ Patch failed: {msg}")
            # Add patch error to history
            if proj not in state.error_history:
                state.error_history[proj] = []
            state.error_history[proj].append(f"Patch application failed: {msg}")
    else:
        print(f"[{proj}] ℹ️ No diff returned; proceeding to tests unchanged.")

    # Run tests
    passed, out = run_pytest(proj)
    state.last_test_output[proj] = out
    
    if passed:
        print(f"[{proj}] ✅ Tests passed!")
        state.completed[proj] = True
    else:
        print(f"[{proj}] ❌ Tests failing. Iteration {iters+1}/{MAX_AGENT_ITERS}.")
        state.iterations[proj] = iters + 1
        
        # Add test failure to error history (only if not a patch error)
        if not patch_error:
            if proj not in state.error_history:
                state.error_history[proj] = []
            
            # Extract key error information from test output
            error_summary = extract_test_error_summary(out)
            state.error_history[proj].append(f"Test failures: {error_summary}")

    return state

def extract_test_error_summary(test_output: str) -> str:
    """Extract a concise summary of test errors."""
    lines = test_output.split('\n')
    errors = []
    
    # Look for common pytest error patterns
    for i, line in enumerate(lines):
        # Failed test cases
        if 'FAILED' in line and '::' in line:
            errors.append(line.strip())
        # Assertion errors
        elif 'AssertionError' in line:
            errors.append(line.strip())
        # Import errors
        elif 'ImportError' in line or 'ModuleNotFoundError' in line:
            errors.append(line.strip())
        # Syntax errors
        elif 'SyntaxError' in line:
            errors.append(line.strip())
    
    if errors:
        return '; '.join(errors[:3])  # Limit to first 3 errors to keep it concise
    else:
        # Fallback: return last few lines if no specific errors found
        return '; '.join([line.strip() for line in lines[-3:] if line.strip()])

def node_advance(state: AgentState) -> AgentState:
    if state.current_idx >= len(state.projects):
        return state
    proj = state.projects[state.current_idx]
    done = state.completed.get(proj, False)
    exhausted = state.iterations.get(proj, 0) >= MAX_AGENT_ITERS
    if done or exhausted:
        state.current_idx += 1
    return state

# ---------- Graph Wiring ----------
def build_graph():
    g = StateGraph(AgentState)
    g.add_node("discover", node_discover)
    g.add_node("analyze_and_patch", node_analyze_and_patch)
    g.add_node("advance", node_advance)

    g.set_entry_point("discover")
    g.add_edge("discover", "analyze_and_patch")
    g.add_edge("analyze_and_patch", "advance")

    def should_continue(state: AgentState) -> str:
        return "analyze_and_patch" if state.current_idx < len(state.projects) else END

    g.add_conditional_edges("advance", should_continue, {
        "analyze_and_patch": "analyze_and_patch",
        END: END
    })
    return g.compile()

def main():
    run_id = f"run_{int(time.time())}"
    print(f"🚀 Mini Coding Agent starting (run_id={run_id})")
    graph = build_graph()
    init = AgentState(run_id=run_id)
    graph.invoke(init)
    print("🎉 All done.")

if __name__ == "__main__":
    main()