import os
import re
import sys
import argparse

def lint_architecture(root_dir):
    """
    Heuristic scanner to detect layer violations.
    Looks for database/server-side imports inside UI/Component folders.
    """
    print(f"--- 🏛️ Architectural Guardian: Linting {root_dir} ---")
    
    ui_dirs = {'components', 'views', 'pages', 'ui', 'screens'}
    db_keywords = {'sql', 'prisma', 'mongoose', 'typeorm', 'postgres', 'database', 'db'}
    
    violations = 0
    
    for root, dirs, files in os.walk(root_dir):
        if 'node_modules' in root or '.git' in root or '.venv' in root:
            continue
            
        # Check if we are inside a UI directory
        path_parts = set(root.split(os.sep))
        if ui_dirs.intersection(path_parts):
            for file in files:
                if not file.endswith(('.js', '.ts', '.jsx', '.tsx', '.py')):
                    continue
                    
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                        
                    for i, line in enumerate(lines):
                        line_lower = line.lower()
                        # Detect imports
                        if 'import ' in line_lower or 'require(' in line_lower:
                            # Check for DB keywords in the import statement
                            if any(kw in line_lower for kw in db_keywords):
                                print(f"🚨 [VIOLATION] {os.path.relpath(filepath, root_dir)} (Line {i+1})")
                                print(f"   Code: {line.strip()}")
                                print(f"   Issue: UI component appears to directly import database/server logic.")
                                violations += 1
                except Exception as e:
                    pass
                    
    print(f"\n--- 🏁 Architectural Linting Complete ---")
    if violations == 0:
        print("✅ No critical layer violations detected.")
    else:
        print(f"❌ Found {violations} potential layer violations. Refactor to Service Layer.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Lint architecture for layer violations")
    parser.add_argument("dir", nargs="?", default=".", help="Directory to scan")
    args = parser.parse_args()
    
    lint_architecture(args.dir)
