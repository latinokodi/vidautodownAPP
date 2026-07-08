import sys
import argparse
import json

KNOWLEDGE = {
    "ladder": [
        {"level": 1, "name": "Basic CLI", "desc": "Flags, commands, plain stdout/stderr.", "tools": "argparse, click"},
        {"level": 2, "name": "Enhanced CLI", "desc": "Colors, spinners, tables, progress bars.", "tools": "rich, chalk, ora, lipgloss"},
        {"level": 3, "name": "Interactive Prompt CLI", "desc": "Selectable menus, wizards, fuzzy search.", "tools": "questionary, inquirer, enquirer, survey"},
        {"level": 4, "name": "Full TUI App", "desc": "Panes, reactive state, live refresh, full-screen.", "tools": "textual, ink, bubbletea, prompt_toolkit"}
    ],
    "stacks": {
        "python": {
            "best_for": "Rich input and fast productivity",
            "tui": "Textual / prompt_toolkit",
            "output": "Rich",
            "prompts": "Questionary",
            "extras": "Pygments, wcwidth"
        },
        "nodejs": {
            "best_for": "Ecosystem familiarity and prompt-heavy tools",
            "tui": "Ink / blessed",
            "output": "Chalk / Ora / Boxen",
            "prompts": "Enquirer / Inquirer",
            "extras": "Commander"
        },
        "go": {
            "best_for": "Robust full-screen apps and single binary",
            "tui": "Bubble Tea",
            "output": "Lip Gloss",
            "prompts": "Survey",
            "extras": "Cobra / Viper"
        }
    }
}

def recommend(query):
    query = query.lower()
    
    # Simple keyword matching for stack
    stack = "python" # Default
    if "node" in query or "js" in query or "javascript" in query:
        stack = "nodejs"
    elif "go" in query or "golang" in query:
        stack = "go"
    
    # Determine Level
    level = 2
    if any(k in query for k in ["full", "tui", "app", "pane", "layout", "reactive"]):
        level = 4
    elif any(k in query for k in ["prompt", "wizard", "menu", "select", "input"]):
        level = 3
    elif any(k in query for k in ["basic", "simple", "flag"]):
        level = 1

    s_info = KNOWLEDGE["stacks"][stack]
    l_info = KNOWLEDGE["ladder"][level-1]

    print(f"\n🚀 TUI PRO MAX RECOMMENDATION")
    print(f"=====================================")
    print(f"Project Query: {query}")
    print(f"Target Stack : {stack.upper()} ({s_info['best_for']})")
    print(f"Target Level : Level {level} - {l_info['name']}")
    print(f"Description  : {l_info['desc']}")
    print(f"\n🛠️ RECOMMENDED STACK")
    print(f"-------------------------------------")
    print(f"Layout/TUI   : {s_info['tui']}")
    print(f"Output/Style : {s_info['output']}")
    print(f"Prompts      : {s_info['prompts']}")
    print(f"Extras       : {s_info['extras']}")
    print(f"\n✅ ACTION PLAN")
    print(f"1. Initialize {stack} project.")
    
    tools = []
    if stack == "python":
        tools = ["textual", "rich", "prompt_toolkit", "questionary"]
    elif stack == "nodejs":
        tools = ["ink", "chalk", "ora", "enquirer"]
    elif stack == "go":
        tools = ["bubbletea", "lipgloss", "survey"]
        
    print(f"2. Install: {', '.join(tools)}")
    print(f"3. Apply Level {level} patterns: {l_info['desc']}")
    print(f"=====================================\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='TUI UX Pro Max Recommendation Tool')
    parser.add_argument('query', help='Project description or keywords')
    args = parser.parse_args()
    
    recommend(args.query)
