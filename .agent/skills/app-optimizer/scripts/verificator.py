import subprocess
import sys
import argparse

def run_verificator(test_command):
    """
    Executes a test command. If it fails, prompts an automatic rollback (via git checkout).
    """
    print(f"--- 🛡️ The Verificator: Running Verification Loop ---")
    print(f"Executing: {test_command}\n")
    
    try:
        result = subprocess.run(test_command, shell=True, text=True)
        
        if result.returncode == 0:
            print("\n✅ Verification Passed. Optimization is stable.")
            return True
        else:
            print(f"\n❌ Verification Failed (Exit Code: {result.returncode}).")
            print("🚨 Optimization broke the application.")
            
            # Auto-Revert Logic
            print("Attempting automatic rollback via 'git restore .'...")
            rollback = subprocess.run("git restore .", shell=True, capture_output=True, text=True)
            if rollback.returncode == 0:
                print("⏪ Rollback successful. Codebase restored to previous state.")
            else:
                print("⚠️ Rollback failed. Please check git status manually.")
            return False
            
    except Exception as e:
        print(f"❌ Verificator Error: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run tests and auto-revert on failure")
    parser.add_argument("command", help="Test command to run (e.g., 'npm test' or 'pytest')")
    args = parser.parse_args()
    
    run_verificator(args.command)
