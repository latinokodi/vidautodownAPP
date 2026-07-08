import os
import json

def analyze_stack(root_dir):
    print(f"--- 🔍 Stack Appraisal: Identifying Technology DNA in {root_dir} ---")
    
    findings = {
        "frontend": [],
        "backend": [],
        "database": [],
        "language": [],
        "build_tools": []
    }
    
    # 1. Check for Node.js / Web
    pkg_json = os.path.join(root_dir, 'package.json')
    if os.path.exists(pkg_json):
        try:
            with open(pkg_json, 'r') as f:
                data = json.load(f)
                deps = {**data.get('dependencies', {}), **data.get('devDependencies', {})}
                
                if 'react' in deps: findings["frontend"].append("React")
                if 'next' in deps: findings["frontend"].append("Next.js")
                if 'vue' in deps: findings["frontend"].append("Vue")
                if 'express' in deps: findings["backend"].append("Express (Legacy)")
                if 'hono' in deps: findings["backend"].append("Hono (Modern)")
                if 'fastify' in deps: findings["backend"].append("Fastify")
                if 'typescript' in deps: findings["language"].append("TypeScript")
                else: findings["language"].append("JavaScript")
                
                if 'vite' in deps: findings["build_tools"].append("Vite")
                if 'webpack' in deps: findings["build_tools"].append("Webpack (Legacy)")
        except:
            pass

    # 2. Check for Python
    req_txt = os.path.join(root_dir, 'requirements.txt')
    pyproject = os.path.join(root_dir, 'pyproject.toml')
    if os.path.exists(req_txt) or os.path.exists(pyproject):
        findings["language"].append("Python")
        # Check content for frameworks
        content = ""
        if os.path.exists(req_txt):
            with open(req_txt, 'r') as f: content = f.read().lower()
        
        if 'flask' in content: findings["backend"].append("Flask (Legacy)")
        if 'django' in content: findings["backend"].append("Django")
        if 'fastapi' in content: findings["backend"].append("FastAPI (Modern)")

    # 3. Recommendations Logic
    print("\n📦 [DETECTED STACK]")
    for cat, items in findings.items():
        if items:
            print(f"  - {cat.capitalize()}: {', '.join(set(items))}")

    print("\n💡 [UPGRADE PATHS & ROI]")
    recommendations = []
    
    if "Express (Legacy)" in findings["backend"]:
        recommendations.append({
            "target": "Hono or Fastify",
            "reason": "Express is slow and lacks native TS support. Hono is 10x faster and Edge-ready.",
            "roi": "HIGH"
        })
    
    if "JavaScript" in findings["language"] and "TypeScript" not in findings["language"]:
        recommendations.append({
            "target": "TypeScript",
            "reason": "JavaScript lacks type safety, leading to production runtime errors.",
            "roi": "CRITICAL"
        })

    if "Webpack (Legacy)" in findings["build_tools"]:
        recommendations.append({
            "target": "Vite",
            "reason": "Webpack has slow HMR and complex config. Vite provides instant dev starts.",
            "roi": "MEDIUM (DevEx Focus)"
        })

    if "Flask (Legacy)" in findings["backend"]:
        recommendations.append({
            "target": "FastAPI",
            "reason": "Flask is synchronous. FastAPI provides async support and auto-Swagger docs.",
            "roi": "HIGH"
        })

    if not recommendations:
        print("  ✅ Stack looks modern and optimized. No major porting suggested.")
    else:
        for rec in recommendations:
            print(f"  🚩 [PORT TO {rec['target']}]")
            print(f"     Why: {rec['reason']}")
            print(f"     ROI: {rec['roi']}\n")

if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    analyze_stack(target)
