# cli_ui.py
import os
from pathlib import Path
from agent import build_graph, safe_get, MAX_ITERATIONS, PROJECTS_DIR

def run_agent_for_project(project: Path):
    graph = build_graph()
    iteration = 0
    state = {"project": project}

    while iteration < MAX_ITERATIONS:
        print(f"\n--- Iteration {iteration + 1} ---")
        state = graph.invoke(state)

        print("\nRequirements:\n", safe_get(state, "requirements", ""))
        print("\nPlan:\n", safe_get(state, "plan", ""))
        print("\nCode Proposal:\n", safe_get(state, "code", ""))
        print("\nError Analysis:\n", safe_get(state, "error_analysis", ""))
        print("\nFix Proposal:\n", safe_get(state, "fix", ""))
        print("\nValidation:\n", safe_get(state, "validation", ""))

        if safe_get(state, "tests_passed", False):
            print(f"\n🎉 All tests passed for {project.name}!")
            break
        else:
            print(f"\n❌ Tests still failing. Iterating again...")
            iteration += 1

def main():
    projects = [p for p in PROJECTS_DIR.iterdir() if p.is_dir()]
    if not projects:
        print("⚠️ No projects found in the 'projects/' directory.")
        return

    print("=== Mini Coding Agent CLI ===\n")
    for idx, proj in enumerate(projects, 1):
        print(f"{idx}. {proj.name}")

    choice = input("\nSelect a project number to run: ")
    try:
        idx = int(choice) - 1
        if idx < 0 or idx >= len(projects):
            print("⚠️ Invalid selection.")
            return
    except ValueError:
        print("⚠️ Please enter a number.")
        return

    project = projects[idx]
    print(f"\n🚀 Running agent for project '{project.name}'...\n")
    run_agent_for_project(project)

if __name__ == "__main__":
    main()
