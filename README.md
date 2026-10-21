# FinRule — Compiler-Driven Financial Modeling DSL & SaaS Studio

**Course:** 4CS501CC25 – Principles of Compiler Design  
**Project Title:** FinRule (ModelScript DSL)  
**Specification Reference:** SRS v2.0  

---

## Architecture Overview

FinRule implements an end-to-end Domain-Specific Language (DSL) for financial modeling with a complete 6-phase compiler pipeline:

1. **Lexical Analysis (Lexer)**: Tokenizes ModelScript code with line/column coordinates, typed tokens, and comment stripping (`//`, `/* */`, `#`).
2. **Syntax Analysis (Recursive Descent Parser)**: Generates a typed Abstract Syntax Tree (AST) representing models, scenarios, loops, conditionals, assignments, and output directives.
3. **Semantic Analyzer & Symbol Table**: Resolves nested scopes (`global`, `model`, `loop`, `scenario`), performs static type checking, validates loop bounds, checks constant division-by-zero, and verifies built-in financial function arity.
4. **Intermediate Representation (IR Generator)**: Linearizes AST into Three-Address Code (TAC) / Quadruples (`OP, arg1, arg2, result`) with temporary variables (`t1, t2...`) and branch labels (`L0, L1...`).
5. **Interpreter / Execution Engine**: Executes models period-by-period, executes scenario variable overrides, computes summary metrics, and generates time-series tabular projections.
6. **Compiler Studio**: Live interactive UI inspector for tokens, AST nodes, symbol tables, IR instructions, and microsecond phase benchmarks.

---

## Project Structure

```
FinRule/
├── finny/                   # Python Virtual Environment
├── requirements.txt         # Python dependencies
├── req.txt                  # Shortcut alias for requirements.txt
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI application & lifespan
│   │   ├── config.py        # Settings & JWT config
│   │   ├── auth_utils.py    # JWT & bcrypt password hashing
│   │   ├── templates_data.py # 5 Predefined financial models
│   │   ├── db/
│   │   │   └── database.py  # Async DB (MongoDB Atlas Motor + Local JSON failover)
│   │   ├── models/
│   │   │   └── schemas.py   # Pydantic request & response models
│   │   ├── routes/
│   │   │   ├── auth.py      # /api/auth
│   │   │   ├── projects.py  # /api/projects
│   │   │   ├── models.py    # /api/models & versions
│   │   │   ├── compiler.py  # /api/execute
│   │   │   ├── executions.py # /api/executions
│   │   │   └── templates.py # /api/templates
│   │   └── compiler/        # The 6-Phase Compiler Pipeline
│   │       ├── tokens.py
│   │       ├── lexer.py
│   │       ├── ast_nodes.py
│   │       ├── parser.py
│   │       ├── semantic.py
│   │       ├── ir.py
│   │       ├── interpreter.py
│   │       ├── builtins.py
│   │       ├── diagnostics.py
│   │       └── pipeline.py
│   └── tests/
│       └── test_compiler.py # Pytest test suite for all compiler phases
└── frontend/                # React + TypeScript + Monaco Editor + Vite
    ├── src/
    │   ├── api/client.ts
    │   ├── compiler/modelscriptMonaco.ts
    │   ├── components/
    │   │   ├── Header.tsx
    │   │   ├── Sidebar.tsx
    │   │   ├── ResultsPanel.tsx
    │   │   ├── TemplatesModal.tsx
    │   │   └── VersionModal.tsx
    │   ├── App.tsx
    │   ├── index.css
    │   └── main.tsx
    ├── package.json
    └── vite.config.ts
```

---

## Terminal Commands

### 1. Backend Setup & Run

Open a terminal in the root folder (`FinRule`):

```bash
# 1. Activate the virtual environment
.\finny\Scripts\Activate.ps1
# On CMD: finny\Scripts\activate.bat
# On Git Bash / Linux: source finny/Scripts/activate

# 2. Install dependencies (from req.txt or requirements.txt)
pip install -r req.txt

# 3. Run the compiler test suite (Optional - verifies all 6 phases)
pytest backend/tests

# 4. Start the FastAPI backend server (Runs on http://localhost:8000)
uvicorn backend.app.main:app --reload --port 8000
```

### 2. Frontend Setup & Run

Open a second terminal in the `frontend` folder (`FinRule/frontend`):

```bash
# 1. Navigate to the frontend directory
cd frontend

# 2. Install frontend dependencies (if not already installed)
npm install --legacy-peer-deps

# 3. Start the Vite React development server
npm run dev
```

The application will be live at: **`http://localhost:5173`**  
API Documentation (Swagger UI) is available at: **`http://localhost:8000/docs`**
