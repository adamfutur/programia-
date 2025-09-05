# run_tests.py
import os
import subprocess
from pathlib import Path
import sys

def run_command(command, cwd):
    """Run a command in the specified directory and return the result"""
    process = subprocess.run(
        command,
        cwd=cwd,
        shell=True,
        text=True,
        capture_output=True
    )
    return process

def print_separator(text):
    """Print a separator with text"""
    print(f"\n{'='*80}\n{text}\n{'='*80}")

def main():
    # Get the absolute path to the projects directory
    base_dir = Path(__file__).parent
    projects_dir = base_dir / 'projects'

    # Test commands for each project
    test_configs = {
        'flask-easy': 'python -m pytest --junitxml=unit.xml',
        'flask-intermediate': 'python -m pytest --junitxml=unit.xml',
        'flask-hard': 'flask --app manage.py test'
    }

    all_passed = True
    results = {}

    # Run tests for each project
    for project, command in test_configs.items():
        project_dir = projects_dir / project
        print_separator(f"Running tests for project: {project}")
        
        # Run the test command
        result = run_command(command, str(project_dir))
        results[project] = result
        
        # Print output
        print("\nOutput:")
        print(result.stdout)
        
        if result.stderr:
            print("\nErrors:")
            print(result.stderr)
        
        # Check if tests passed
        if result.returncode != 0:
            all_passed = False

    # Print final summary
    print_separator("Test Summary")
    for project, result in results.items():
        status = "PASSED" if result.returncode == 0 else "FAILED"
        print(f"{project}: {status}")

    # Exit with appropriate status code
    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    main()