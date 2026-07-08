import os
import re
import sys

def scan_dead_code(root_dir):
    """
    Scans for potentially unused files and patterns.
    Note: This is a heuristic scanner.
    """
    print(f"--- 🕵️ Scanning for Project Waste in {root_dir} ---")
    
    # Files to ignore
    ignored_dirs = {'.git', 'node_modules', '.venv', 'dist', 'build', '__pycache__', '.next'}
    
    all_files = []
    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in ignored_dirs]
        for file in files:
            all_files.append(os.path.join(root, file))

    # Heuristic: Unused assets
    asset_exts = {'.png', '.jpg', '.jpeg', '.svg', '.gif', '.webp', '.avif'}
    code_exts = {'.js', '.jsx', '.ts', '.tsx', '.py', '.html', '.css', '.scss'}
    
    assets = [f for f in all_files if os.path.splitext(f)[1].lower() in asset_exts]
    code_files = [f for f in all_files if os.path.splitext(f)[1].lower() in code_exts]
    
    print(f"Found {len(assets)} assets and {len(code_files)} code files.")
    
    # Read all code content once
    combined_code = ""
    for cf in code_files:
        try:
            with open(cf, 'r', encoding='utf-8', errors='ignore') as f:
                combined_code += f.read()
        except:
            pass

    # Check for unused assets
    unused_assets = []
    for asset in assets:
        basename = os.path.basename(asset)
        if basename not in combined_code:
            unused_assets.append(asset)

    if unused_assets:
        print("\n🚩 [POTENTIALLY UNUSED ASSETS]")
        for ua in unused_assets:
            print(f"  - {os.path.relpath(ua, root_dir)}")
    else:
        print("\n✅ All assets appear to be referenced.")

    # Check for common "TODO" and "FIXME" debt
    print("\n📝 [TECHNICAL DEBT MARKERS]")
    debt_found = False
    for cf in code_files:
        try:
            with open(cf, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                matches = re.findall(r'//\s*(TODO|FIXME|HACK):?.*', content, re.I)
                if matches:
                    debt_found = True
                    print(f"  - {os.path.relpath(cf, root_dir)}: {len(matches)} markers found.")
        except:
            pass
    if not debt_found:
        print("  ✅ No TODO/FIXME markers found.")

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    scan_dead_code(target)
