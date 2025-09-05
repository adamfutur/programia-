# Mini Coding Agent

Implement a coding agent using Python and your preferred agentic framework like LangGraph, CrewAI, etc. The agent should analyse and implement the project requirements from the various projects present under the `projects/` directory.

## Overview

The agent goes through the projects in the `projects/` directory, each project potentially using different programming languages and frameworks. The agent should,

- Read the README.md file of each project to understand the requirements
- Implement any missing functionality like APIs, functions, models, etc....
- Runs unit tests available at each project to validate the correctness of the implementations.
- Be able to handle various programming languages and frameworks.

The agent should be able to handle various implementation needs such as but not limited to:

- Implementing API endpoints and routes
- Implementing function and method definitions
- Implement data models and schemas
- Define utility functions and helpers

## High Level Structure

```
mini-coding-agent/
├── agent.py (implement your agent here)
├── tests.py (for running all the test cases)
├── check_usage.py (for checking LLM resource utilisation)
├── projects
        ├── project_1
                ├── app/
                ├── README.md
        ├── project_2
                ├── app/
                ├── README.md
└── requirements.txt
```

Each project should have:

- A `README.md` file with requirements that needs to be fulfilled.
- A `tests/` directory with unit tests


## Available LLM Models
- You will have access to GPT-4.1-mini and GPT-5-mini OpenAI models to build your agent. You'll already see a OpenAI client initialised with GPT-4.1-mini in the agent.py file.
- To understand the LLM limits and throughputs, run the check_usage.py for more detailed info.


## Programming Language & Framework
The setup comes with Python and LangGraph out of the box. Feel free to install and use your preferred agentic framework.


## Executable Commands

### Install dependencies:

   ```
   pip install -r requirements.txt
   ```

### Run the agent:
   ```
   python agent.py
   ```

### Check LLM Credit Usage:
   ```
   python check_usage.py
   ```

### Run Tests
   ```
   python tests.py     
   ```

### To Move The Project Offline
1. Use the button on the top right corner of the HackerRank platform to switch to the online IDE (if you're currently in the offline + git mode)
2. Use Ctrl + J (Windows/Linux) or Cmd + J to view the panel.
3. You'll find a terminal window.
4. Run the following commands on the terminal
   ```
   env | grep OPENAI
   ```
5. Copy and set the following variables in your local machine
   ```
   OPENAI_API_BASE
   OPENAI_API_KEY
   ```
6. Now, toggle back to offline mode using the button at the top right corner of the HackerRank platform.
7. You'll be presented with your dedicated git repo URL.
8. Clone this repo to your local and start making changes to the same.
9. Once your development is done, commit your changes and push them back to the server.
10. Remember to submit your solution on the HackerRank platform once it's done.
