# 🚀 Mini Coding Agent

An AI-powered coding assistant that can automatically analyze, implement, and fix code for projects inside the `projects/` directory.

Supports Python, Node.js, and Java projects out of the box.

Perfect for hackathons — it doesn’t just fix your code, it also generates a Judge Standout Summary to impress the judges with a polished explanation of what was improved.

## ✨ Features

*   ✅ Detects project language (Python, Node.js, Java)
*   ✅ Reads `README.md` to extract requirements
*   ✅ Generates missing functionality (APIs, functions, models, etc.)
*   ✅ Runs tests using the appropriate framework (pytest, npm test, or mvn test)
*   ✅ Automatically fixes failing code iteratively
*   ✅ Provides a final Judge Standout Summary for presentations
*   ✅ Backs up original files before applying fixes

## 📂 Project Structure

```
mini-coding-agent/
├── agent.py              # Main agent implementation
├── requirements.txt      # Python dependencies
├── projects/
│   ├── project_1/
│   │   ├── app/
│   │   ├── README.md
│   │   └── tests/
│   ├── project_2/
│   │   ├── app/
│   │   ├── README.md
│   │   └── tests/
```

Each project must contain:

*   A `README.md` file (project requirements).
*   A `tests/` directory with unit tests.

## 🎨 Design

The Mini Coding Agent is designed with modularity and extensibility in mind. Its core architecture separates language detection, requirement analysis, code generation, testing, and reporting into distinct modules. This allows for easy addition of new languages or testing frameworks in the future. The iterative feedback loop between code generation and testing ensures a robust and self-correcting system.

## 💻 Language Used & Tech Stack

*   **Primary Language:** Python
*   **Supported Project Languages:** Python, Node.js, Java
*   **AI Model Integration:** OpenAI API (configurable for different models like GPT-4.1-mini)
*   **Testing Frameworks:**
    *   Python: `pytest`
    *   Node.js: `npm test` (or equivalent configured in `package.json`)
    *   Java: `mvn test` (Maven)

## ⚡ Installation

Clone the repository:

```bash
git clone https://github.com/yourusername/mini-coding-agent.git
cd mini-coding-agent
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Set your OpenAI credentials:

```bash
export OPENAI_API_KEY="your_api_key"
export OPENAI_API_BASE="https://api.openai.com/v1"
```

(Optional) Configure model and max iterations:

```bash
export OPENAI_MODEL="gpt-4.1-mini"
export MAX_AGENT_ITERS=5
```

## ▶️ Usage

Run the agent across all projects inside `projects/`:

```bash
python agent.py
```

The agent will:

1.  Analyze the project requirements.
2.  Propose a coding plan.
3.  Apply fixes and generate code.
4.  Run tests iteratively until they pass.
5.  Provide a Judge Standout Summary at the end.

## 🧪 Example Run

```
=== Mini Coding Agent ===

🚀 Processing flask-hard...

--- Iteration 1 ---
✅ Updated projects/flask-hard/app.py
✅ Updated projects/flask-hard/log_processor.py
❌ Tests still failing for flask-hard. Iterating again...

--- Iteration 2 ---
🎉 All tests passed for flask-hard!

--- REPORT ---
Requirements:
- API must handle logs
- Tests failing on missing endpoint

Plan:
- Fix log_processor.py
- Add missing API route in app.py

Validation:
✅ All tests passed

💡 Judge Standout Summary:
The agent fixed missing API routes, implemented log processing, and ensured full test coverage.
This makes the project production-ready and highlights automated debugging with AI.
```

## 🏆 Why This Stands Out in Hackathons

*   **Multi-language support** → Works on Python, Node.js, and Java.
*   **Autonomous fixing** → Iterates automatically until all tests pass.
*   **Judge Standout Summary** → Automatically generates a polished project explanation, saving time for demo day.

## 📜 License

MIT License.
