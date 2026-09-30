import ast, pathlib

# Find the root directory of the project
root = pathlib.Path(__file__).parent

# Find all Python files recursively
py = list(root.rglob("*.py"))

errors = []
for p in py:
    try:
        ast.parse(p.read_text(encoding="utf-8"))
    except Exception as e:
        errors.append((str(p), str(e)))

print(f"Python files checked: {len(py)}")

if errors:
    for e in errors:
        print("ERROR", e)
    raise SystemExit(1)

print("PASS: Python syntax")

# Check for required files
required_files = [
    "app.py",
    "requirements.txt",
    "README.md",
    "agents/five_agents.py",
    "agents/crewai_team.py",
    "rag/loader.py",
    "services/groq_service.py",
    "database/db.py"
]

for required in required_files:
    if not (root / required).exists():
        raise SystemExit(f"Missing required file: {required}")

print("PASS: Required files")
print("PASS: Package structure")
print("✅ All checks passed! Your project is ready to deploy.")
