# agent.py
import os
import re
import json
import glob
import time
import shutil
import subprocess
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Any
from enum import Enum

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
TEST_TIMEOUT_SECS = int(os.getenv("TEST_TIMEOUT_SECS", "120"))
RUN_DIR = os.getenv("AGENT_RUN_DIR", ".agent_runs")
os.makedirs(RUN_DIR, exist_ok=True)

# ---------- OpenAI Client ----------
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
)

# ---------- Phase Definitions ----------
class Phase(Enum):
    UNDERSTAND = "understand"
    PLAN = "plan"
    CODE = "code"
    IDENTIFY_ERRORS = "identify_errors"
    FIX_ERRORS = "fix_errors"
    VALIDATE = "validate"

# ---------- Problem Analysis Classes ----------
@dataclass
class ProblemLocation:
    file_path: str
    line_number: Optional[int] = None
    function_name: Optional[str] = None
    class_name: Optional[str] = None
    problem_type: str = "unknown"
    description: str = ""

@dataclass
class ProblemAnalysis:
    problems: List[ProblemLocation] = field(default_factory=list)
    summary: str = ""
    priority: str = "medium"

# ---------- Utilities ----------
def read_file(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"

def write_file(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def list_text_files(base: str) -> List[str]:
    exts = (".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go", ".rs", ".rb", ".php", ".kt", ".swift", ".c", ".h", ".cpp", ".md", ".toml", ".yaml", ".yml", ".json")
    paths = []
    for root, _, files in os.walk(base):
        if any(part in root for part in (".git", ".venv", "node_modules", "__pycache__", ".pytest_cache", "dist", "build")):
            continue
        for fn in files:
            if fn.endswith(exts):
                paths.append(os.path.join(root, fn))
    return paths

def get_project_files_content(proj_path: str, max_files: int = 20) -> str:
    """Get content of key project files."""
    files_content = []
    text_files = list_text_files(proj_path)
    
    # Prioritize certain file types
    priority_patterns = ['requirements', 'setup', 'package', 'main', 'app', 'init', 'test', 'config']
    priority_files = []
    other_files = []
    
    for file_path in text_files:
        filename = os.path.basename(file_path).lower()
        if any(pattern in filename for pattern in priority_patterns):
            priority_files.append(file_path)
        else:
            other_files.append(file_path)
    
    selected_files = priority_files[:max_files//2] + other_files[:max_files//2]
    
    for file_path in selected_files[:max_files]:
        rel_path = os.path.relpath(file_path, proj_path)
        try:
            content = read_file(file_path)
            files_content.append(f"=== {rel_path} ===\n{content[:1500]}{'...[truncated]' if len(content) > 1500 else ''}\n")
        except Exception as e:
            files_content.append(f"=== {rel_path} ===\n[Error reading file: {e}]\n")
    
    return "\n".join(files_content)

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

        # For new files, create directory structure
        if not os.path.exists(target_path):
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            original = ""
        else:
            original = read_file(target_path)
            
        lines = original.splitlines(keepends=True) if original else []
        new_lines, idx = [], 0

        try:
            for hunk in patched_file:
                while idx < hunk.source_start - 1:
                    if idx < len(lines):
                        new_lines.append(lines[idx])
                    idx += 1
                for line in hunk:
                    if line.is_added:
                        new_lines.append(line.value)
                    elif line.is_removed:
                        idx += 1
                    else:
                        if idx < len(lines):
                            new_lines.append(lines[idx])
                        idx += 1
            while idx < len(lines):
                new_lines.append(lines[idx])
                idx += 1
        except Exception as e:
            return False, [], f"❌ Failed applying hunk to {rel_path}: {e}"

        write_file(target_path, "".join(new_lines))
        changed.append(rel_path)

    return True, changed, f"🛠 Patched {len(changed)} files."

def run_pytest(project_path: str, timeout: int = TEST_TIMEOUT_SECS) -> Tuple[bool, str]:
    if not os.path.isdir(project_path):
        return False, f"❌ Project path not found: {project_path}"

    # Check if pytest is available
    try:
        cmd = ["pytest", "-v", "--tb=short"]
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
        
    except FileNotFoundError:
        # Fallback to python -m pytest
        try:
            cmd = ["python", "-m", "pytest", "-v", "--tb=short"]
            proc = subprocess.Popen(
                cmd,
                cwd=project_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            out, _ = proc.communicate(timeout=timeout)
            passed = proc.returncode == 0
            return passed, out
        except:
            return False, "❌ pytest not available"

def discover_projects(root: str = PROJECTS_ROOT) -> List[str]:
    projs = []
    for p in glob.glob(os.path.join(root, "*")):
        if os.path.isdir(p) and os.path.exists(os.path.join(p, "README.md")):
            # Check if there are tests (either tests directory or test files)
            has_tests = os.path.isdir(os.path.join(p, "tests")) or any(
                "test" in f.lower() for f in os.listdir(p) if f.endswith('.py')
            )
            if has_tests:
                projs.append(p)
    return sorted(projs)

def log_usage(run_id: str, usage: Dict):
    path = os.path.join(RUN_DIR, "usage.jsonl")
    rec = {"ts": time.time(), "run_id": run_id, **usage}
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")

def analyze_test_output_for_problems(test_output: str, project_path: str) -> ProblemAnalysis:
    """Analyze test output to identify specific problems and their locations."""
    analysis = ProblemAnalysis()
    problems = []
    
    # Patterns to detect file paths and line numbers in test output
    patterns = [
        r'File "([^"]+)", line (\d+)',
        r'([\w\/\.\-_]+\.py):(\d+)',
        r'at ([\w\/\.\-_]+\.py):(\d+)',
        r'in ([\w\/\.\-_]+\.py)',
        r'([\w\/\.\-_]+\.py)',
    ]
    
    # Common error types
    error_types = {
        'ImportError': 'import',
        'ModuleNotFoundError': 'import',
        'AttributeError': 'attribute',
        'NameError': 'name',
        'TypeError': 'type',
        'ValueError': 'value',
        'SyntaxError': 'syntax',
        'AssertionError': 'logic',
        'KeyError': 'key',
        'IndexError': 'index',
        'RuntimeError': 'runtime'
    }
    
    lines = test_output.split('\n')
    current_error_type = "unknown"
    
    for i, line in enumerate(lines):
        # Detect error type
        for error_name, error_type in error_types.items():
            if error_name in line:
                current_error_type = error_type
                break
        
        # Find file locations
        for pattern in patterns:
            matches = re.findall(pattern, line)
            for match in matches:
                if isinstance(match, tuple):
                    file_path, line_num = match[0], match[1]
                else:
                    file_path, line_num = match, None
                
                # Make path absolute
                if not os.path.isabs(file_path):
                    file_path = os.path.join(project_path, file_path)
                
                if os.path.exists(file_path) or any(os.path.exists(os.path.join(project_path, f)) for f in os.listdir(project_path) if f in file_path):
                    problem = ProblemLocation(
                        file_path=file_path,
                        line_number=int(line_num) if line_num and line_num.isdigit() else None,
                        problem_type=current_error_type,
                        description=line.strip()[:200]
                    )
                    problems.append(problem)
    
    # Deduplicate problems
    unique_problems = []
    seen_locations = set()
    for problem in problems:
        loc_key = f"{problem.file_path}:{problem.line_number}"
        if loc_key not in seen_locations:
            unique_problems.append(problem)
            seen_locations.add(loc_key)
    
    analysis.problems = unique_problems
    
    # Create summary
    if unique_problems:
        file_counts = {}
        for problem in unique_problems:
            rel_path = os.path.basename(problem.file_path)
            file_counts[rel_path] = file_counts.get(rel_path, 0) + 1
        
        summary_parts = []
        for file_path, count in sorted(file_counts.items(), key=lambda x: x[1], reverse=True):
            summary_parts.append(f"{file_path} ({count} issues)")
        
        analysis.summary = "Problem files: " + ", ".join(summary_parts[:3])
        
        # Set priority
        if any(p.problem_type in ['syntax', 'import'] for p in unique_problems):
            analysis.priority = 'high'
        elif any(p.problem_type in ['name', 'type', 'value'] for p in unique_problems):
            analysis.priority = 'medium'
        else:
            analysis.priority = 'low'
    
    return analysis

def get_file_context(file_path: str, line_number: Optional[int] = None, context_lines: int = 5) -> str:
    """Get context around a specific line in a file."""
    if not os.path.exists(file_path):
        return f"File not found: {file_path}"
    
    try:
        content = read_file(file_path)
        lines = content.split('\n')
        
        if line_number is None:
            return f"File: {file_path}\nContent:\n{content[:1000]}..."
        
        start = max(0, line_number - context_lines - 1)
        end = min(len(lines), line_number + context_lines)
        
        context = []
        for i in range(start, end):
            marker = ">>> " if i + 1 == line_number else "    "
            context.append(f"{marker}{i+1:4d}: {lines[i]}")
        
        return f"File: {file_path}\nContext around line {line_number}:\n" + "\n".join(context)
    
    except Exception as e:
        return f"Error reading file {file_path}: {e}"

# ---------- Phase-Specific Prompts ----------
UNDERSTAND_PROMPT = """You are an expert coding agent. Analyze the project requirements and current state.

PROJECT README:
{readme}

FILE TREE:
{tree}

KEY FILES CONTENT:
{files}

INITIAL TEST RESULTS:
{test_output}

PROBLEM ANALYSIS:
{problem_analysis}

{previous_context}

Provide a comprehensive analysis of:
1. Project requirements and objectives
2. Current implementation status
3. Missing functionality
4. Key files that need work
5. Test expectations

Be specific and focus on actionable insights."""

PLAN_PROMPT = """Create a detailed implementation plan based on the requirements analysis.

REQUIREMENTS ANALYSIS:
{understanding}

PROBLEM ANALYSIS:
{problem_analysis}

Create a step-by-step plan addressing:
1. Files to create/modify (with specific paths)
2. Functions/classes to implement (with signatures)
3. API endpoints/routes needed
4. Data models/schemas required
5. Dependencies and imports
6. Test implementation strategy

Be extremely specific about file names, function names, and implementation details."""

CODE_PROMPT = """Implement the solution using a unified diff patch format.

REQUIREMENTS:
{understanding}

IMPLEMENTATION PLAN:
{plan}

Generate ONLY a valid unified diff patch that:
1. Creates new files if needed
2. Modifies existing files as specified in the plan
3. Implements all required functionality
4. Includes proper error handling
5. Follows Python best practices
6. Satisfies test requirements

Output only the diff, no explanations or additional text."""

IDENTIFY_ERRORS_PROMPT = """Analyze test failures and identify specific issues.

CURRENT IMPLEMENTATION:
{understanding}

TEST RESULTS:
{test_output}

FILE CONTEXT:
{file_context}

{previous_context}

Identify:
1. Specific errors and their root causes
2. Missing implementations with file locations
3. Syntax/logic errors with line numbers
4. Import/dependency issues
5. Test expectation mismatches

Be specific about file paths, line numbers, and exact issues."""

FIX_ERRORS_PROMPT = """Fix the identified errors with a targeted patch.

ERROR ANALYSIS:
{error_analysis}

PROBLEM LOCATIONS:
{problem_locations}

FILE CONTEXT:
{file_context}

PREVIOUS CONTEXT:
{previous_context}

Generate ONLY a unified diff patch that fixes the specific issues.
Focus on precise corrections in the mentioned files and lines.
Ensure fixes address root causes and maintain code quality.
Output only the diff, no explanations."""

# ---------- Agent State ----------
@dataclass
class ProjectState:
    path: str
    phase: Phase = Phase.UNDERSTAND
    iterations: int = 0
    completed: bool = False
    understanding: str = ""
    plan: str = ""
    error_analysis: str = ""
    last_test_output: str = ""
    problem_analysis: ProblemAnalysis = field(default_factory=ProblemAnalysis)
    previous_context: List[str] = field(default_factory=list)

@dataclass
class AgentState:
    run_id: str
    projects: List[str] = field(default_factory=list)
    current_idx: int = 0
    project_states: Dict[str, ProjectState] = field(default_factory=dict)

# ---------- LangGraph Nodes ----------
def node_discover(state: AgentState) -> AgentState:
    if not state.projects:
        state.projects = discover_projects(PROJECTS_ROOT)
        print(f"🔍 Discovered {len(state.projects)} projects: {[os.path.basename(p) for p in state.projects]}")
        # Initialize project states
        for proj in state.projects:
            state.project_states[proj] = ProjectState(path=proj)
    return state

def call_openai(messages: List[Dict], phase: str, project: str, run_id: str) -> str:
    """Call OpenAI API and log usage."""
    try:
        resp = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=messages,
            temperature=0.1,
            max_tokens=4000
        )

        content = resp.choices[0].message.content or ""
        usage = getattr(resp, "usage", None)
        if usage:
            log_usage(run_id, {
                "project": os.path.basename(project),
                "prompt_tokens": usage.prompt_tokens,
                "completion_tokens": usage.completion_tokens,
                "total_tokens": usage.total_tokens,
                "model": DEFAULT_MODEL,
                "phase": phase
            })
        
        return content
    except Exception as e:
        return f"API Error: {e}"

def node_understand_requirements(state: AgentState) -> AgentState:
    if state.current_idx >= len(state.projects):
        return state
    
    proj = state.projects[state.current_idx]
    proj_state = state.project_states[proj]
    
    if proj_state.phase != Phase.UNDERSTAND:
        return state
    
    project_name = os.path.basename(proj)
    print(f"\n[{project_name}] 🔍 Analyzing requirements...")
    
    # Read project files
    readme_path = os.path.join(proj, "README.md")
    readme = read_file(readme_path) if os.path.exists(readme_path) else "No README found"
    
    tree = "\n".join(sorted(os.listdir(proj)))
    files = get_project_files_content(proj)
    
    # Run initial tests to understand current state
    passed, test_output = run_pytest(proj)
    proj_state.last_test_output = test_output
    
    # Analyze test output for problems
    proj_state.problem_analysis = analyze_test_output_for_problems(test_output, proj)
    
    previous_context = "\n".join([f"Previous attempt {i+1}:\n{ctx}" for i, ctx in enumerate(proj_state.previous_context)])
    
    user_msg = UNDERSTAND_PROMPT.format(
        readme=readme,
        tree=tree, 
        files=files,
        test_output=test_output[:1000] + "... [truncated]" if len(test_output) > 1000 else test_output,
        problem_analysis=proj_state.problem_analysis.summary,
        previous_context=previous_context
    )
    
    understanding = call_openai([{"role": "user", "content": user_msg}], "understand", proj, state.run_id)
    proj_state.understanding = understanding
    proj_state.phase = Phase.PLAN
    
    print(f"[{project_name}] ✅ Requirements analyzed")
    if proj_state.problem_analysis.problems:
        print(f"   📊 Found {len(proj_state.problem_analysis.problems)} issues in {len(set(p.file_path for p in proj_state.problem_analysis.problems))} files")
    
    return state

def node_plan_approach(state: AgentState) -> AgentState:
    if state.current_idx >= len(state.projects):
        return state
    
    proj = state.projects[state.current_idx]
    proj_state = state.project_states[proj]
    
    if proj_state.phase != Phase.PLAN:
        return state
    
    project_name = os.path.basename(proj)
    print(f"[{project_name}] 📋 Creating implementation plan...")
    
    user_msg = PLAN_PROMPT.format(
        understanding=proj_state.understanding,
        problem_analysis=proj_state.problem_analysis.summary
    )
    
    plan = call_openai([{"role": "user", "content": user_msg}], "plan", proj, state.run_id)
    proj_state.plan = plan
    proj_state.phase = Phase.CODE
    
    print(f"[{project_name}] ✅ Implementation plan created")
    return state

def node_write_code(state: AgentState) -> AgentState:
    if state.current_idx >= len(state.projects):
        return state
    
    proj = state.projects[state.current_idx]
    proj_state = state.project_states[proj]
    
    if proj_state.phase != Phase.CODE:
        return state
    
    project_name = os.path.basename(proj)
    print(f"[{project_name}] 💻 Generating code...")
    
    user_msg = CODE_PROMPT.format(
        understanding=proj_state.understanding,
        plan=proj_state.plan
    )
    
    code_response = call_openai([{"role": "user", "content": user_msg}], "code", proj, state.run_id)
    
    diff_text = clean_diff_text(code_response)
    if diff_text:
        ok, changed, msg = apply_unified_diff(proj, diff_text)
        if ok:
            print(f"[{project_name}] {msg}")
            if changed:
                changed_files = [os.path.basename(f) for f in changed[:3]]
                print(f"   📝 Modified: {', '.join(changed_files)}{'...' if len(changed) > 3 else ''}")
        else:
            print(f"[{project_name}] ⚠️ Patch application failed: {msg}")
            proj_state.previous_context.append(f"Code generation failed: {msg}")
    else:
        print(f"[{project_name}] ⚠️ No valid diff generated")
    
    proj_state.phase = Phase.VALIDATE
    print(f"[{project_name}] ✅ Code generation completed")
    return state

def node_identify_errors(state: AgentState) -> AgentState:
    if state.current_idx >= len(state.projects):
        return state
    
    proj = state.projects[state.current_idx]
    proj_state = state.project_states[proj]
    
    if proj_state.phase != Phase.IDENTIFY_ERRORS:
        return state
    
    project_name = os.path.basename(proj)
    print(f"[{project_name}] 🔍 Analyzing errors...")
    
    # Get file context for problematic files
    file_contexts = []
    for problem in proj_state.problem_analysis.problems[:3]:
        context = get_file_context(problem.file_path, problem.line_number)
        file_contexts.append(context)
    
    file_context = "\n\n".join(file_contexts)
    
    previous_context = "\n".join([f"Previous attempt {i+1}:\n{ctx}" for i, ctx in enumerate(proj_state.previous_context)])
    
    user_msg = IDENTIFY_ERRORS_PROMPT.format(
        understanding=proj_state.understanding,
        test_output=proj_state.last_test_output,
        file_context=file_context,
        previous_context=previous_context
    )
    
    error_analysis = call_openai([{"role": "user", "content": user_msg}], "identify_errors", proj, state.run_id)
    proj_state.error_analysis = error_analysis
    proj_state.phase = Phase.FIX_ERRORS
    
    print(f"[{project_name}] ✅ Error analysis completed")
    return state

def node_fix_errors(state: AgentState) -> AgentState:
    if state.current_idx >= len(state.projects):
        return state
    
    proj = state.projects[state.current_idx]
    proj_state = state.project_states[proj]
    
    if proj_state.phase != Phase.FIX_ERRORS:
        return state
    
    project_name = os.path.basename(proj)
    print(f"[{project_name}] 🔧 Fixing errors...")
    
    # Get file context for problematic files
    file_contexts = []
    problem_locations = []
    for problem in proj_state.problem_analysis.problems[:3]:
        context = get_file_context(problem.file_path, problem.line_number)
        file_contexts.append(context)
        rel_path = os.path.basename(problem.file_path)
        problem_locations.append(f"{rel_path}:{problem.line_number} - {problem.problem_type}")
    
    file_context = "\n\n".join(file_contexts)
    problem_locations_str = "\n".join(problem_locations)
    
    previous_context = "\n".join([f"Previous attempt {i+1}:\n{ctx}" for i, ctx in enumerate(proj_state.previous_context)])
    
    user_msg = FIX_ERRORS_PROMPT.format(
        error_analysis=proj_state.error_analysis,
        problem_locations=problem_locations_str,
        file_context=file_context,
        previous_context=previous_context
    )
    
    fix_response = call_openai([{"role": "user", "content": user_msg}], "fix_errors", proj, state.run_id)
    
    diff_text = clean_diff_text(fix_response)
    if diff_text:
        ok, changed, msg = apply_unified_diff(proj, diff_text)
        if ok:
            print(f"[{project_name}] {msg}")
            if changed:
                changed_files = [os.path.basename(f) for f in changed[:3]]
                print(f"   🔧 Fixed: {', '.join(changed_files)}{'...' if len(changed) > 3 else ''}")
        else:
            print(f"[{project_name}] ⚠️ Fix application failed: {msg}")
    
    proj_state.phase = Phase.VALIDATE
    print(f"[{project_name}] ✅ Error fixing completed")
    return state

def node_validate(state: AgentState) -> AgentState:
    if state.current_idx >= len(state.projects):
        return state
    
    proj = state.projects[state.current_idx]
    proj_state = state.project_states[proj]
    
    if proj_state.phase != Phase.VALIDATE:
        return state
    
    project_name = os.path.basename(proj)
    print(f"[{project_name}] ✅ Running validation tests...")
    
    # Run tests
    passed, test_output = run_pytest(proj)
    proj_state.last_test_output = test_output
    
    # Update problem analysis
    proj_state.problem_analysis = analyze_test_output_for_problems(test_output, proj)
    
    if passed:
        print(f"[{project_name}] 🎉 All tests passed!")
        proj_state.completed = True
        
        # Show success summary
        if proj_state.problem_analysis.problems:
            print(f"   ✅ Successfully resolved issues")
        
        return state
    else:
        print(f"[{project_name}] ❌ Tests failed.")
        
        # Show current problems
        if proj_state.problem_analysis.problems:
            print(f"   📊 Current issues:")
            for i, problem in enumerate(proj_state.problem_analysis.problems[:2]):
                rel_path = os.path.basename(problem.file_path)
                line_info = f":{problem.line_number}" if problem.line_number else ""
                print(f"      {i+1}. {rel_path}{line_info} - {problem.problem_type}")
        
        proj_state.iterations += 1
        
        if proj_state.iterations >= MAX_AGENT_ITERS:
            print(f"[{project_name}] ⚠️ Max iterations reached ({MAX_AGENT_ITERS})")
            proj_state.completed = False
            return state
        
        # Add current attempt to context and restart error identification
        attempt_summary = f"Iteration {proj_state.iterations} - Test failures detected"
        proj_state.previous_context.append(attempt_summary)
        proj_state.phase = Phase.IDENTIFY_ERRORS
        
        print(f"[{project_name}] 🔄 Re-analyzing errors...")
    
    return state

def node_advance(state: AgentState) -> AgentState:
    if state.current_idx >= len(state.projects):
        return state
    
    proj = state.projects[state.current_idx]
    proj_state = state.project_states[proj]
    
    if proj_state.completed or proj_state.iterations >= MAX_AGENT_ITERS:
        state.current_idx += 1
        project_name = os.path.basename(proj)
        status = "COMPLETED" if proj_state.completed else "FAILED"
        print(f"[{project_name}] ➡️ Moving to next project ({status})")
    
    return state

# ---------- Graph Wiring ----------
def build_graph():
    g = StateGraph(AgentState)
    
    # Add all nodes
    g.add_node("discover", node_discover)
    g.add_node("understand", node_understand_requirements)
    g.add_node("plan", node_plan_approach)
    g.add_node("code", node_write_code)
    g.add_node("identify_errors", node_identify_errors)
    g.add_node("fix_errors", node_fix_errors)
    g.add_node("validate", node_validate)
    g.add_node("advance", node_advance)
    
    # Set entry point
    g.set_entry_point("discover")
    
    # Linear flow for main phases
    g.add_edge("discover", "understand")
    g.add_edge("understand", "plan")
    g.add_edge("plan", "code")
    g.add_edge("code", "validate")
    g.add_edge("identify_errors", "fix_errors")
    g.add_edge("fix_errors", "validate")
    
    # Conditional routing from validate
    def route_from_validate(state: AgentState) -> str:
        if state.current_idx >= len(state.projects):
            return END
        
        proj = state.projects[state.current_idx]
        proj_state = state.project_states[proj]
        
        if proj_state.completed or proj_state.iterations >= MAX_AGENT_ITERS:
            return "advance"
        elif proj_state.phase == Phase.IDENTIFY_ERRORS:
            return "identify_errors"
        else:
            return "advance"
    
    g.add_conditional_edges("validate", route_from_validate, {
        "identify_errors": "identify_errors",
        "advance": "advance",
        END: END
    })
    
    # Conditional routing from advance
    def route_from_advance(state: AgentState) -> str:
        return "understand" if state.current_idx < len(state.projects) else END
    
    g.add_conditional_edges("advance", route_from_advance, {
        "understand": "understand",
        END: END
    })
    
    return g.compile()

def main():
    run_id = f"run_{int(time.time())}"
    print(f"🚀 MINI CODING AGENT STARTING")
    print(f"📋 Run ID: {run_id}")
    print(f"⚙️  Configuration:")
    print(f"   • Model: {DEFAULT_MODEL}")
    print(f"   • Max Iterations: {MAX_AGENT_ITERS}")
    print(f"   • Test Timeout: {TEST_TIMEOUT_SECS}s")
    print(f"   • Projects Root: {PROJECTS_ROOT}")
    
    print(f"\n🔄 AGENT WORKFLOW:")
    print("   1. Discover projects")
    print("   2. Analyze requirements")
    print("   3. Create implementation plan") 
    print("   4. Generate and apply code")
    print("   5. Run validation tests")
    print("   6. Identify and fix errors")
    print("   7. Repeat until success or max iterations")
    
    print(f"\n" + "="*60)
    
    graph = build_graph()
    init = AgentState(run_id=run_id)
    
    try:
        final_state = graph.invoke(init)
        
        print(f"\n" + "="*60)
        print("🏁 PROCESSING COMPLETE - SUMMARY")
        print("="*60)
        
        completed_count = 0
        failed_count = 0
        
        for proj, proj_state in final_state.project_states.items():
            project_name = os.path.basename(proj)
            if proj_state.completed:
                print(f"✅ {project_name}: SUCCESS")
                completed_count += 1
            else:
                print(f"❌ {project_name}: FAILED (after {proj_state.iterations} iterations)")
                failed_count += 1
        
        total = completed_count + failed_count
        success_rate = (completed_count / total * 100) if total > 0 else 0
        
        print(f"\n📊 RESULTS:")
        print(f"   • Total: {total}")
        print(f"   • ✅ Success: {completed_count}")
        print(f"   • ❌ Failed: {failed_count}") 
        print(f"   • 📈 Success Rate: {success_rate:.1f}%")
        
        print(f"\n💾 Logs saved to: {RUN_DIR}")
        print("🎉 Agent execution completed!")
        
    except Exception as e:
        print(f"❌ Agent execution failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()