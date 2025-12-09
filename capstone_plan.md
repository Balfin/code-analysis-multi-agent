# AI-Powered Code Analysis Multi-Agent System: Implementation Plan

## Overview

![AI-Powered Code Analysis Multi-Agent System Architecture](capstone_project.png)

This implementation plan breaks down the AI-Powered Code Analysis Multi-Agent System into 13 distinct, verifiable phases. The approach follows a bottom-up strategy: establish foundational infrastructure first (environment, core data models), then build the agent orchestration layer, add analysis capabilities, implement persistence, create API endpoints, and finally construct the frontend interfaces. Each phase is independently testable and produces concrete artifacts. The plan assumes parallel work is possible between backend (Phases 1-7) and frontend (Phases 8-11) after Phase 7 completes, with final integration in Phases 12-13.

**Total Phases:** 13  
**Parallelization Opportunity:** Phases 8-11 (frontend) can begin after Phase 7 (backend API) is complete  
**Critical Path:** Phases 1 → 2 → 3 → 4 → 5 → 6 → 7 → 12 → 13

---

## Phase 1: Project Setup & Core Infrastructure

### Goal / Outcome
Establish the project directory structure, install all dependencies, configure the environment, and verify that the basic Python and Node.js ecosystems are functional. The result is a runnable skeleton with no logic, but all imports work.

### Deliverables
- [ ] Complete directory structure matching the project layout
- [ ] `environment.yml` file with all Python dependencies
- [ ] Conda environment created and activated
- [ ] `backend/` directory with `__init__.py` files in all subdirectories
- [ ] `frontend/` directory with React + Vite + Tailwind scaffolding
- [ ] `package.json` with required frontend dependencies
- [ ] `.env.example` file documenting required environment variables
- [ ] Basic `README.md` with setup instructions
- [ ] `.gitignore` file configured for Python, Node, and artifacts
- [ ] `issues/` directory for storing generated reports

### Dependencies & Prerequisites
- Python 3.11+ installed
- Conda or Miniconda installed
- Node.js 18+ and npm installed
- Git initialized in project root
- (Optional) Ollama installed for local LLM, or OpenAI API key for cloud LLM

### Validation Criteria
- Running `conda env list` shows the `code-analyzer` environment
- `conda activate code-analyzer` succeeds
- `python -c "import langchain, langgraph, fastapi"` runs without errors
- `cd frontend && npm install` completes successfully
- `npm run dev` in frontend starts Vite dev server (even if app is empty)
- All `__init__.py` files present in backend subdirectories

### Tests / Checks
```bash
# Test 1: Verify conda environment
conda activate code-analyzer
python --version  # Should show Python 3.11.x

# Test 2: Check Python imports
python -c "import langchain; print(langchain.__version__)"
python -c "import langgraph; print('LangGraph OK')"
python -c "import fastapi; print(fastapi.__version__)"

# Test 3: Check frontend
cd frontend
npm list react vite tailwindcss  # Should show installed versions

# Test 4: Directory structure
ls -la backend/agents backend/tools backend/models backend/prompts
ls -la frontend/src/components

# Test 5: Environment template
cat .env.example  # Should contain placeholders like LANGCHAIN_API_KEY
```

Expected results:
- All Python imports succeed
- Frontend dependencies installed (check `node_modules/` exists)
- Directory structure matches project layout
- No import errors or missing module warnings

### Risks & Mitigations
1. **Risk:** Dependency conflicts in conda environment  
   **Mitigation:** Use exact version pins in `environment.yml`; test on clean conda installation

2. **Risk:** Frontend build tools incompatible with Node version  
   **Mitigation:** Document required Node version (18+); use `.nvmrc` file if needed

3. **Risk:** Missing system dependencies (e.g., Ollama not installed)  
   **Mitigation:** Make Ollama optional in Phase 1; provide fallback to OpenAI API configuration

### Artifacts & Next Steps
**Keep:**
- All directory structure and empty files
- `environment.yml` and `package.json`
- `.env.example` file

**Next:** Proceed to Phase 2 to define core data models and schemas.

---

## Phase 2: Core Data Models & Issue Schema

### Goal / Outcome
Define the Python data models that represent the shared state across agents (AnalysisState) and the issue tracking schema (Issue, IssueStore). These models form the foundation for all agent communication and data persistence. The result is fully type-safe, validated models with unit tests.

### Deliverables
- [ ] `backend/models/issue.py` with complete Issue model (Pydantic)
- [ ] IssueStore class with save, get_all, get_by_id methods
- [ ] AnalysisState TypedDict definition
- [ ] RiskLevel and IssueType enums
- [ ] Issue.to_markdown() method for report generation
- [ ] Unit tests for Issue model (validation, hash generation, serialization)
- [ ] Unit tests for IssueStore (save, retrieve, index updates)
- [ ] Sample test data (at least 3 issue examples)

### Dependencies & Prerequisites
- Phase 1 completed (environment set up)
- `pydantic>=2.0.0` installed
- Python `typing` module understanding (TypedDict, Annotated)

### Validation Criteria
- Issue model validates all required fields
- Issue ID generation is deterministic (same content = same ID)
- IssueStore creates `issues/` directory if it doesn't exist
- Saving an issue creates both `.md` file and updates `index.json`
- Markdown output is properly formatted with code blocks and metadata
- All unit tests pass with 100% coverage of Issue and IssueStore

### Tests / Checks
```bash
# Test 1: Run unit tests
cd backend
python -m pytest models/test_issue.py -v

# Test 2: Manual model validation
python -c "
from models.issue import Issue, RiskLevel, IssueType
issue = Issue(
    location='test.py:10',
    type=IssueType.SECURITY,
    risk_level=RiskLevel.HIGH,
    title='SQL Injection',
    description='User input not sanitized',
    code_snippet='query = f\"SELECT * FROM users WHERE name = {user_input}\"',
    solution='Use parameterized queries'
)
print(issue.id)  # Should print 12-char hash
print(issue.to_markdown()[:50])  # Should print markdown header
"

# Test 3: IssueStore operations
python -c "
from models.issue import IssueStore, Issue, RiskLevel, IssueType
store = IssueStore('./test_issues')
issue = Issue(
    location='test.py:10', type=IssueType.SECURITY,
    risk_level=RiskLevel.HIGH, title='Test Issue',
    description='Test', code_snippet='code', solution='fix'
)
path = store.save(issue)
print(f'Saved to: {path}')
issues = store.get_all()
print(f'Total issues: {len(issues)}')
"

# Test 4: Verify file outputs
ls test_issues/*.md  # Should list saved issues
cat test_issues/index.json  # Should contain JSON array
```

Expected results:
- All pytest tests pass
- Issue model correctly validates fields and rejects invalid data
- IssueStore creates files and index
- Markdown output is readable and well-formatted

### Risks & Mitigations
1. **Risk:** Hash collisions in issue IDs  
   **Mitigation:** Use SHA-256 with location + title + snippet; 12-char prefix provides ~68 billion unique IDs

2. **Risk:** File I/O errors (permissions, disk space)  
   **Mitigation:** Add try/except blocks; test with read-only filesystem to verify error handling

3. **Risk:** JSON serialization issues with datetime  
   **Mitigation:** Use `.isoformat()` for datetime serialization in index updates

### Artifacts & Next Steps
**Keep:**
- `backend/models/issue.py` with full implementation
- Unit test suite in `backend/models/test_issue.py`
- Sample issues in `test_issues/` directory

**Next:** Proceed to Phase 3 to implement code analysis tools.

---

## Phase 3: Code Analysis Tools Implementation

### Goal / Outcome
Build the LangChain tools that agents will use to interact with code: file reading, directory traversal, AST parsing, and pattern matching. Each tool is independently testable and returns structured data. The result is a working toolkit that can analyze Python files.

### Deliverables
- [ ] `backend/tools/code_tools.py` with all tool implementations
- [ ] `read_file(filepath: str)` tool with error handling
- [ ] `list_python_files(directory: str, ignore_patterns: list)` tool
- [ ] `extract_functions(code: str)` tool using AST
- [ ] `find_pattern(code: str, pattern: str)` tool with regex
- [ ] Unit tests for each tool with sample code
- [ ] Test fixture directory with sample Python files
- [ ] Documentation of tool inputs/outputs

### Dependencies & Prerequisites
- Phase 2 completed (data models defined)
- Python `ast` module for parsing
- Python `re` module for regex
- Python `pathlib` for file operations
- `langchain.tools` imported

### Validation Criteria
- `read_file` successfully reads files and handles missing files gracefully
- `list_python_files` excludes ignore patterns (venv, __pycache__, .git)
- `extract_functions` parses valid Python and returns function metadata
- `find_pattern` correctly matches regex patterns with line numbers
- All tools return consistent data structures (lists of dicts)
- Tools handle edge cases (empty files, syntax errors, special characters)

### Tests / Checks
```bash
# Test 1: Create sample code
mkdir -p test_project
cat > test_project/sample.py << 'EOF'
def calculate_sum(a, b):
    return a + b

def unsafe_query(user_input):
    query = f"SELECT * FROM users WHERE id = '{user_input}'"
    return query

API_KEY = "secret-key-12345"
EOF

# Test 2: Test read_file tool
python -c "
from tools.code_tools import read_file
content = read_file('test_project/sample.py')
print(f'Read {len(content)} characters')
assert 'calculate_sum' in content
"

# Test 3: Test list_python_files tool
python -c "
from tools.code_tools import list_python_files
files = list_python_files('test_project')
print(f'Found {len(files)} Python files')
assert 'sample.py' in files[0]
"

# Test 4: Test extract_functions tool
python -c "
from tools.code_tools import read_file, extract_functions
code = read_file('test_project/sample.py')
functions = extract_functions(code)
print(f'Found {len(functions)} functions')
for func in functions:
    print(f'  - {func[\"name\"]} at line {func[\"line_start\"]}')
"

# Test 5: Test find_pattern tool
python -c "
from tools.code_tools import read_file, find_pattern
code = read_file('test_project/sample.py')
matches = find_pattern(code, r'API_KEY.*=.*[\"\\'].*[\"\\']')
print(f'Found {len(matches)} hardcoded secrets')
assert len(matches) >= 1
"

# Test 6: Run full test suite
python -m pytest tools/test_code_tools.py -v
```

Expected results:
- All tools return data without errors
- AST parsing handles valid Python code
- Pattern matching finds expected issues
- Error cases (invalid files, syntax errors) are handled gracefully

### Risks & Mitigations
1. **Risk:** AST parsing fails on complex Python syntax (Python 3.11+ features)  
   **Mitigation:** Use `ast.parse()` with mode='exec'; catch SyntaxError and return error dict

2. **Risk:** Regex patterns too broad or miss edge cases  
   **Mitigation:** Test with diverse code samples; document pattern limitations

3. **Risk:** Large files cause memory issues  
   **Mitigation:** Add file size checks; skip files > 1MB with warning

### Artifacts & Next Steps
**Keep:**
- `backend/tools/code_tools.py` with all tool implementations
- Test suite in `backend/tools/test_code_tools.py`
- Test fixtures in `test_project/`

**Next:** Proceed to Phase 4 to build the LangGraph agent orchestration.

---

## Phase 4: LangGraph Multi-Agent Orchestration

### Goal / Outcome
Implement the LangGraph workflow that coordinates the Manager agent and three specialist agents (Security, Performance, Architecture). The graph defines the state transitions, routing logic, and agent delegation. The result is a working graph that can be invoked end-to-end (even with stub agents).

### Deliverables
- [ ] `backend/agents/graph.py` with complete StateGraph definition
- [ ] `create_analysis_graph()` function returning compiled graph
- [ ] `route_to_analysts()` routing function for conditional edges
- [ ] Manager agent stub (basic delegation logic)
- [ ] Security, Performance, Architecture agent stubs (return mock issues)
- [ ] Results compiler stub (formats final output)
- [ ] Graph visualization (using LangGraph Studio or mermaid diagram)
- [ ] Integration test that runs the full graph with sample state

### Dependencies & Prerequisites
- Phase 3 completed (tools available)
- Phase 2 completed (AnalysisState defined)
- `langgraph>=0.1.0` installed
- Understanding of StateGraph, nodes, edges, conditional routing

### Validation Criteria
- Graph compiles without errors
- Manager agent receives initial state and delegates to specialists
- Each specialist agent is called exactly once per file
- Routing function correctly determines next agent based on state
- Results compiler aggregates all issues from state
- Graph returns final state with scan_status="done"
- No circular loops or deadlocks in graph execution

### Tests / Checks
```bash
# Test 1: Compile graph
python -c "
from agents.graph import create_analysis_graph
graph = create_analysis_graph()
print(f'Graph compiled with {len(graph.nodes)} nodes')
"

# Test 2: Test with minimal state
python -c "
from agents.graph import create_analysis_graph, AnalysisState

graph = create_analysis_graph()
initial_state = AnalysisState(
    target_path='./test_project',
    files_to_analyze=['sample.py'],
    current_file='',
    issues=[],
    messages=[],
    scan_status='pending'
)

result = graph.invoke(initial_state)
print(f'Final status: {result[\"scan_status\"]}')
print(f'Issues found: {len(result[\"issues\"])}')
assert result['scan_status'] == 'done'
"

# Test 3: Verify routing logic
python -c "
from agents.graph import route_to_analysts, AnalysisState

# Test manager routes to security first
state = AnalysisState(
    target_path='.',
    files_to_analyze=['a.py', 'b.py'],
    current_file='a.py',
    issues=[],
    messages=[],
    scan_status='scanning'
)
next_node = route_to_analysts(state)
print(f'Next node: {next_node}')
assert next_node in ['security', 'performance', 'architecture', 'compile']
"

# Test 4: Run integration test
python -m pytest agents/test_graph.py::test_full_workflow -v
```

Expected results:
- Graph compiles and shows correct node count
- Initial state flows through all agents
- Final state has scan_status="done" and some issues (even if mocked)
- No exceptions or hangs during execution

### Risks & Mitigations
1. **Risk:** Infinite loops in routing logic  
   **Mitigation:** Add max_iterations parameter to graph; log each routing decision

2. **Risk:** State mutations not tracked correctly (operator.add not working)  
   **Mitigation:** Test issue accumulation explicitly; verify Annotated[List[dict], operator.add] behavior

3. **Risk:** Agents don't receive full state context  
   **Mitigation:** Log state at entry/exit of each agent; verify state immutability

### Artifacts & Next Steps
**Keep:**
- `backend/agents/graph.py` with complete orchestration
- Agent stubs in `backend/agents/manager.py`, `specialists.py`
- Integration tests in `backend/agents/test_graph.py`

**Next:** Proceed to Phase 5 to implement full specialist agent logic with LLM calls.

---

## Phase 5: Specialist Agents with LLM Integration

### Goal / Outcome
Replace agent stubs with full implementations that use LangChain to call LLMs (Ollama or OpenAI) with specialized prompts. Each agent analyzes code using tools and returns structured issues. The result is working agents that produce real code analysis.

### Deliverables
- [ ] `backend/agents/specialists.py` with full Security, Performance, Architecture agents
- [ ] `backend/prompts/templates.py` with all expert prompts
- [ ] LLM initialization code (supports both Ollama and OpenAI)
- [ ] Agent output parsing (LLM response → Issue objects)
- [ ] Prompt engineering documentation
- [ ] Test cases with real code samples and expected issues
- [ ] LangSmith tracing configuration for debugging
- [ ] Configuration file (`backend/config.py`) with API keys

### Dependencies & Prerequisites
- Phase 4 completed (graph orchestration works)
- Phase 3 completed (tools available)
- Ollama running locally OR OpenAI API key configured
- `langchain-community` or `langchain-openai` installed
- LangSmith API key (optional but recommended)

### Validation Criteria
- Each agent successfully calls LLM with code and returns issues
- Security agent finds SQL injection, hardcoded secrets, XSS
- Performance agent finds N+1 queries, blocking operations
- Architecture agent finds SOLID violations, code duplication
- Issues have all required fields (location, risk_level, title, description, solution)
- Agents use tools (read_file, extract_functions) before LLM call
- LangSmith tracing shows agent execution flow

### Tests / Checks
```bash
# Test 1: Configure LLM
cat > backend/config.py << 'EOF'
import os
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "code-analyzer-capstone"
# os.environ["LANGCHAIN_API_KEY"] = "your-key"  # Add if using LangSmith
EOF

# Test 2: Start Ollama (if using local LLM)
ollama serve &
ollama pull llama3

# Test 3: Test Security agent
python -c "
from agents.specialists import security_agent
from agents.graph import AnalysisState

state = AnalysisState(
    target_path='.',
    files_to_analyze=['test_project/sample.py'],
    current_file='test_project/sample.py',
    issues=[],
    messages=[],
    scan_status='scanning'
)

result = security_agent(state)
print(f'Security issues found: {len([i for i in result[\"issues\"] if i[\"type\"]==\"security\"])}')
for issue in result['issues']:
    print(f'  - {issue[\"title\"]} ({issue[\"risk_level\"]})')
"

# Test 4: Test Performance agent
python -c "
from agents.specialists import performance_agent
# ... similar test with performance-specific code
"

# Test 5: Test Architecture agent
python -c "
from agents.specialists import architecture_agent
# ... similar test with architecture-specific code
"

# Test 6: Run full agent test suite
python -m pytest agents/test_specialists.py -v --tb=short

# Test 7: Check LangSmith traces
# Open https://smith.langchain.com and verify traces appear
```

Expected results:
- LLM calls succeed (no timeout or API errors)
- Agents return issues in correct format
- Sample vulnerable code triggers appropriate security issues
- LangSmith dashboard shows execution traces (if configured)

### Risks & Mitigations
1. **Risk:** LLM rate limits or timeouts  
   **Mitigation:** Add retry logic with exponential backoff; implement request queuing

2. **Risk:** LLM output not structured (doesn't follow JSON schema)  
   **Mitigation:** Use function calling or structured output features; add fallback parsing

3. **Risk:** High token costs with OpenAI  
   **Mitigation:** Use Ollama for development; add token usage logging

### Artifacts & Next Steps
**Keep:**
- `backend/agents/specialists.py` with full implementations
- `backend/prompts/templates.py` with all prompts
- `backend/config.py` with LangSmith configuration
- Test suite with real code analysis examples

**Next:** Proceed to Phase 6 to implement results compilation and state management.

---

## Phase 6: Results Compilation & Manager Agent

### Goal / Outcome
Implement the Manager agent that orchestrates file processing and the Results Compiler that aggregates all findings into a summary report. The Manager decides which files to analyze and when to compile results. The result is end-to-end code analysis with summary generation.

### Deliverables
- [ ] `backend/agents/manager.py` with full Manager agent logic
- [ ] `backend/agents/compiler.py` with Results Compiler implementation
- [ ] Manager routing logic (iterate through files, then compile)
- [ ] Results Compiler prompt template for summary generation
- [ ] Code health score calculation
- [ ] Priority grouping (Critical/High/Medium/Low)
- [ ] Integration test: analyze multi-file project end-to-end
- [ ] Issue persistence integration (save all issues to filesystem)

### Dependencies & Prerequisites
- Phase 5 completed (specialist agents work)
- Phase 4 completed (graph orchestration)
- Phase 2 completed (IssueStore available)
- Understanding of state management and iteration

### Validation Criteria
- Manager processes all files in files_to_analyze list
- Manager routes to each specialist agent for each file
- Manager transitions to results_compiler after all files processed
- Results Compiler aggregates issues from all files
- Summary report includes executive summary, critical issues, health score
- All issues saved to `issues/` directory with index updated
- Final state contains complete summary in messages

### Tests / Checks
```bash
# Test 1: Create multi-file test project
mkdir -p test_project_multi
cat > test_project_multi/auth.py << 'EOF'
def authenticate(username, password):
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    return query  # SQL injection vulnerability
EOF

cat > test_project_multi/api.py << 'EOF'
def slow_endpoint(items):
    results = []
    for item in items:
        # N+1 query pattern
        detail = db.query(f"SELECT * FROM details WHERE id={item.id}")
        results.append(detail)
    return results
EOF

# Test 2: Run full analysis
python -c "
from agents.graph import create_analysis_graph, AnalysisState
from tools.code_tools import list_python_files

graph = create_analysis_graph()
files = list_python_files('test_project_multi')

initial_state = AnalysisState(
    target_path='test_project_multi',
    files_to_analyze=files,
    current_file='',
    issues=[],
    messages=[],
    scan_status='pending'
)

result = graph.invoke(initial_state)
print(f'Analyzed {len(files)} files')
print(f'Found {len(result[\"issues\"])} total issues')
print(f'Summary: {result[\"messages\"][-1][\"content\"][:200]}...')
assert result['scan_status'] == 'done'
assert len(result['issues']) > 0
"

# Test 3: Verify issue persistence
ls issues/*.md  # Should list all saved issues
cat issues/index.json | python -m json.tool  # Should be valid JSON

# Test 4: Check summary quality
python -c "
from agents.graph import create_analysis_graph, AnalysisState

# ... run analysis ...
summary = result['messages'][-1]['content']
assert 'Critical' in summary or 'High' in summary  # Should mention priorities
assert 'Security' in summary or 'Performance' in summary  # Should mention categories
print('Summary quality check passed')
"
```

Expected results:
- All files in test project analyzed
- Issues found in multiple categories
- Summary report generated with structure (executive summary, by priority)
- All issues persisted to filesystem

### Risks & Mitigations
1. **Risk:** Manager gets stuck processing same file repeatedly  
   **Mitigation:** Track processed files in state; remove from files_to_analyze after completion

2. **Risk:** Results Compiler overwhelmed by too many issues (context limit)  
   **Mitigation:** Summarize top 20 issues by priority; provide issue counts by category

3. **Risk:** State size grows too large with many files  
   **Mitigation:** Clear messages array periodically; keep only essential data

### Artifacts & Next Steps
**Keep:**
- `backend/agents/manager.py` with full implementation
- `backend/agents/compiler.py` with summary generation
- Integration tests for multi-file analysis
- Sample analyzed project in `test_project_multi/`

**Next:** Proceed to Phase 7 to build the FastAPI backend.

---

## Phase 7: FastAPI Backend & REST API

### Goal / Outcome
Create the FastAPI application with REST endpoints for starting analysis, retrieving issues, and chatting about findings. The backend exposes the LangGraph workflow via HTTP and provides CRUD operations for issues. The result is a testable API that can be called from any HTTP client.

### Deliverables
- [ ] `backend/app.py` with complete FastAPI application
- [ ] POST `/analyze` endpoint to start code analysis
- [ ] GET `/issues` endpoint with filtering (type, risk_level)
- [ ] GET `/issues/{issue_id}` endpoint for issue details
- [ ] POST `/chat` endpoint for Q&A about issues
- [ ] CORS middleware configuration for frontend
- [ ] Error handling and validation
- [ ] API documentation (auto-generated by FastAPI)
- [ ] Health check endpoint (`GET /health`)
- [ ] Unit tests for all endpoints

### Dependencies & Prerequisites
- Phase 6 completed (full agent workflow works)
- `fastapi>=0.111.0` installed
- `uvicorn>=0.30.0` installed
- Understanding of async/await in Python
- Pydantic models for request/response validation

### Validation Criteria
- FastAPI app starts without errors on port 8000
- `/analyze` endpoint accepts path and returns analysis summary
- `/issues` endpoint returns list of issues with filtering
- `/issues/{issue_id}` returns full markdown content
- `/chat` endpoint uses LLM to answer questions about issues
- CORS configured to allow frontend origin (http://localhost:5173)
- API docs accessible at `http://localhost:8000/docs`
- All endpoints return proper HTTP status codes

### Tests / Checks
```bash
# Test 1: Start backend
cd backend
uvicorn app:app --reload &
sleep 3  # Wait for startup

# Test 2: Test health endpoint
curl http://localhost:8000/health
# Expected: {"status": "healthy"}

# Test 3: Test analyze endpoint
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"path": "./test_project_multi", "file_types": ["*.py"]}'
# Expected: {"status": "completed", "issues_found": <number>, "summary": "..."}

# Test 4: Test issues list endpoint
curl http://localhost:8000/issues
# Expected: {"issues": [...], "total": <number>}

# Test 5: Test issues filtering
curl "http://localhost:8000/issues?type=security&risk_level=high"
# Expected: Filtered list of high-risk security issues

# Test 6: Test issue detail endpoint
ISSUE_ID=$(curl http://localhost:8000/issues | python -c "import sys, json; print(json.load(sys.stdin)['issues'][0]['id'])")
curl http://localhost:8000/issues/$ISSUE_ID
# Expected: {"id": "...", "content": "# Issue Title\n..."}

# Test 7: Test chat endpoint
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What are the most critical issues?", "context": null}'
# Expected: {"response": "..."}

# Test 8: Run API tests
python -m pytest tests/test_api.py -v

# Test 9: Check API docs
curl http://localhost:8000/docs  # Should return HTML
```

Expected results:
- All endpoints respond with valid JSON
- Analysis endpoint processes code and returns issues
- Filtering works correctly
- Chat endpoint provides helpful responses
- API documentation is accessible

### Risks & Mitigations
1. **Risk:** Synchronous graph.invoke() blocks FastAPI event loop  
   **Mitigation:** Use `run_in_executor` or implement async graph execution

2. **Risk:** Long-running analysis times out HTTP request  
   **Mitigation:** Return 202 Accepted immediately; provide status polling endpoint

3. **Risk:** CORS errors prevent frontend access  
   **Mitigation:** Test with curl -H "Origin: http://localhost:5173"; verify CORS headers

### Artifacts & Next Steps
**Keep:**
- `backend/app.py` with all endpoints
- API test suite in `tests/test_api.py`
- Running backend server (keep for frontend development)

**Next:** Proceed to Phase 8 to build React frontend structure. Phases 8-11 can proceed in parallel if desired.

---

## Phase 8: React Frontend - Core Structure & Routing

### Goal / Outcome
Set up the React application with Vite, Tailwind CSS, and component structure. Implement the main App component with navigation between Dashboard, Issues, and Chat views. The result is a navigable UI skeleton with no backend integration yet.

### Deliverables
- [ ] `frontend/` directory fully initialized with Vite + React
- [ ] `tailwind.config.js` configured with custom theme
- [ ] `frontend/src/App.jsx` with navigation and view switching
- [ ] `frontend/src/index.css` with Tailwind imports
- [ ] `frontend/src/components/` directory structure
- [ ] Component files: AnalysisDashboard.jsx, IssuesList.jsx, ChatPanel.jsx (stubs)
- [ ] Header with app branding and navigation
- [ ] Responsive layout (works on mobile/desktop)
- [ ] Unit tests for App component (renders without crashing)

### Dependencies & Prerequisites
- Phase 7 completed (backend API available for testing)
- Node.js 18+ and npm installed
- `react`, `react-dom`, `vite`, `tailwindcss` dependencies
- `lucide-react` for icons (or alternative icon library)

### Validation Criteria
- `npm run dev` starts development server on port 5173
- App renders with header and three navigation buttons
- Clicking navigation buttons switches between views
- Tailwind classes apply correctly (colors, spacing)
- No console errors in browser
- App is responsive (test at 320px, 768px, 1920px widths)

### Tests / Checks
```bash
# Test 1: Initialize frontend
cd frontend
npm create vite@latest . -- --template react
npm install
npm install -D tailwindcss postcss autoprefixer lucide-react
npx tailwindcss init -p

# Test 2: Configure Tailwind
cat > tailwind.config.js << 'EOF'
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        zinc: {
          950: '#09090b',
        }
      }
    },
  },
  plugins: [],
}
EOF

# Test 3: Start dev server
npm run dev
# Visit http://localhost:5173 in browser

# Test 4: Visual inspection checklist
# - [ ] Header appears with "Code Analyzer" branding
# - [ ] Three navigation buttons: Dashboard, Issues, Chat
# - [ ] Clicking buttons switches views
# - [ ] Dark theme (zinc-950 background) applies
# - [ ] No layout shift or flickering

# Test 5: Test responsive design
# In browser DevTools, toggle device toolbar
# Test at widths: 375px (mobile), 768px (tablet), 1920px (desktop)

# Test 6: Run component tests (if using Vitest)
npm run test
```

Expected results:
- Development server runs without errors
- Navigation works smoothly
- Tailwind styling applies correctly
- No visual glitches or console errors

### Risks & Mitigations
1. **Risk:** Tailwind CSS not applying (PostCSS config issue)  
   **Mitigation:** Verify `@tailwind` directives in index.css; check postcss.config.js exists

2. **Risk:** Component imports fail (path resolution)  
   **Mitigation:** Use relative imports; configure Vite aliases if needed

3. **Risk:** Icon library missing or incompatible  
   **Mitigation:** Test lucide-react imports; have fallback to emoji icons

### Artifacts & Next Steps
**Keep:**
- `frontend/` with all configuration and component stubs
- Running dev server (keep for rapid iteration)

**Next:** Proceed to Phase 9 to implement the Analysis Dashboard with backend integration.

---

## Phase 9: Analysis Dashboard with Real-Time Updates

### Goal / Outcome
Build the Analysis Dashboard that allows users to input a codebase path, start analysis, and see real-time progress. Integrate with the `/analyze` endpoint and display results (issue counts by type). The result is a functional dashboard that triggers analysis and shows outcomes.

### Deliverables
- [ ] `frontend/src/components/AnalysisDashboard.jsx` fully implemented
- [ ] Path input field with validation
- [ ] "Start Analysis" button with loading state
- [ ] Progress display (status, current file, issue count)
- [ ] Results summary cards (Security, Performance, Architecture counts)
- [ ] Error handling (display API errors to user)
- [ ] API client utility (`src/api/client.js`)
- [ ] Integration test (mock API, verify UI updates)

### Dependencies & Prerequisites
- Phase 8 completed (React app structure exists)
- Phase 7 completed (backend API running)
- `fetch` API understanding (or axios if preferred)
- React hooks: useState, useEffect

### Validation Criteria
- Input field accepts valid paths
- Start button triggers POST to `/analyze` endpoint
- Progress updates display during analysis (if polling implemented)
- Results cards show correct issue counts
- Errors display in user-friendly format
- Dashboard gracefully handles slow or failed API responses

### Tests / Checks
```bash
# Test 1: Implement API client
cat > frontend/src/api/client.js << 'EOF'
const API_BASE = 'http://localhost:8000';

export async function startAnalysis(path) {
  const response = await fetch(`${API_BASE}/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path, file_types: ['*.py'] })
  });
  if (!response.ok) throw new Error('Analysis failed');
  return response.json();
}
EOF

# Test 2: Test in browser
# 1. Start backend: cd backend && uvicorn app:app --reload
# 2. Start frontend: cd frontend && npm run dev
# 3. Open http://localhost:5173
# 4. Enter path: "./test_project_multi"
# 5. Click "Start Analysis"
# 6. Verify:
#    - Button shows "Analyzing..." state
#    - Progress updates appear (if implemented)
#    - Results cards populate after completion

# Test 3: Test error handling
# 1. Stop backend server
# 2. Try to start analysis
# 3. Verify error message appears in UI

# Test 4: Test with invalid path
# 1. Enter non-existent path
# 2. Start analysis
# 3. Verify backend returns appropriate error

# Test 5: Manual integration test
# Follow full user flow:
# - Open dashboard
# - Enter valid project path
# - Start analysis
# - Wait for completion
# - Verify results appear
# - Check Network tab for API calls
```

Expected results:
- Analysis triggers successfully
- UI updates reflect analysis state
- Results display with correct numbers
- Errors are user-friendly

### Risks & Mitigations
1. **Risk:** CORS errors when calling backend  
   **Mitigation:** Verify backend CORS middleware includes frontend origin

2. **Risk:** Analysis takes too long, user sees no feedback  
   **Mitigation:** Implement progress polling or WebSocket (Phase 10 optional)

3. **Risk:** Race conditions if user clicks "Start" multiple times  
   **Mitigation:** Disable button during analysis; use loading state

### Artifacts & Next Steps
**Keep:**
- `frontend/src/components/AnalysisDashboard.jsx` with full implementation
- `frontend/src/api/client.js` with API utilities
- Integration test checklist

**Next:** Proceed to Phase 10 to build the Issues List view.

---

## Phase 10: Issues List & Detail View

### Goal / Outcome
Create the Issues List component that fetches issues from the backend, displays them in a filterable/sortable list, and shows full issue details when selected. The result is a complete issues browser with filtering by type and risk level.

### Deliverables
- [ ] `frontend/src/components/IssuesList.jsx` fully implemented
- [ ] Issue list with filtering controls (type, risk level)
- [ ] Issue cards with priority badges
- [ ] Selected issue detail panel (markdown rendering)
- [ ] API integration: GET `/issues` and GET `/issues/{id}`
- [ ] Loading and error states
- [ ] Responsive split view (list + detail)
- [ ] Unit tests for filtering logic

### Dependencies & Prerequisites
- Phase 9 completed (dashboard works)
- Phase 7 completed (issues API available)
- `marked` library for markdown rendering (or alternative)
- React state management for selected issue

### Validation Criteria
- Issues load from backend on component mount
- Filters correctly query backend with parameters
- Issue cards display title, risk level, location
- Clicking issue loads full detail in right panel
- Markdown content renders properly (headers, code blocks)
- Empty state shown when no issues found
- Loading spinner appears during data fetch

### Tests / Checks
```bash
# Test 1: Install markdown library
cd frontend
npm install marked

# Test 2: Create sample issues for testing
# Run backend analysis first to populate issues/
cd backend
python -c "
from agents.graph import create_analysis_graph, AnalysisState
from tools.code_tools import list_python_files

graph = create_analysis_graph()
files = list_python_files('test_project_multi')
state = AnalysisState(
    target_path='test_project_multi',
    files_to_analyze=files,
    current_file='',
    issues=[],
    messages=[],
    scan_status='pending'
)
result = graph.invoke(state)
print(f'Created {len(result[\"issues\"])} sample issues')
"

# Test 3: Test in browser
# 1. Navigate to "Issues" tab
# 2. Verify list of issues appears
# 3. Click different filters (security, performance, architecture)
# 4. Click an issue
# 5. Verify detail panel shows markdown content

# Test 4: Test API calls in Network tab
# Verify:
# - GET /issues called on mount
# - GET /issues?type=security called when filter applied
# - GET /issues/{id} called when issue clicked

# Test 5: Test edge cases
# - No issues: verify empty state message
# - Slow network: verify loading spinner
# - Failed fetch: verify error message

# Test 6: Visual QA checklist
# - [ ] Risk level badges color-coded (critical=red, high=orange, medium=yellow, low=green)
# - [ ] List scrolls independently from detail
# - [ ] Selected issue highlighted in list
# - [ ] Markdown renders code blocks with syntax highlighting
```

Expected results:
- Issues display correctly in list
- Filtering updates list in real-time
- Issue details render markdown properly
- All states (loading, error, empty) handled

### Risks & Mitigations
1. **Risk:** Too many issues cause performance lag  
   **Mitigation:** Implement virtual scrolling or pagination (limit to 50 issues per page)

2. **Risk:** Markdown rendering security (XSS)  
   **Mitigation:** Use sanitized markdown renderer; never use dangerouslySetInnerHTML without sanitization

3. **Risk:** Issue detail panel too narrow on mobile  
   **Mitigation:** Switch to stacked layout on small screens

### Artifacts & Next Steps
**Keep:**
- `frontend/src/components/IssuesList.jsx` with full implementation
- Updated API client with issues endpoints

**Next:** Proceed to Phase 11 to implement the Chat interface.

---

## Phase 11: Chat Interface for Issue Q&A

### Goal / Outcome
Build the Chat Panel that allows users to ask questions about code issues using natural language. Integrate with the `/chat` endpoint and display conversation history. The result is an interactive chat interface for issue exploration.

### Deliverables
- [ ] `frontend/src/components/ChatPanel.jsx` fully implemented
- [ ] Message history display (user messages + assistant responses)
- [ ] Input field with send button
- [ ] Context banner showing current issue (if selected)
- [ ] API integration: POST `/chat`
- [ ] Loading state (typing indicator)
- [ ] Auto-scroll to latest message
- [ ] Message timestamps (optional)
- [ ] Unit tests for message handling

### Dependencies & Prerequisites
- Phase 10 completed (issues list works)
- Phase 7 completed (chat API available)
- React state for message history
- Understanding of async LLM responses

### Validation Criteria
- Chat input accepts text and sends to backend
- Messages display in correct order (chronological)
- Assistant responses appear after user messages
- Issue context passed to backend if issue selected
- Loading state prevents multiple simultaneous requests
- Conversation history persists during session
- Messages auto-scroll to bottom on new message

### Tests / Checks
```bash
# Test 1: Test in browser
# 1. Navigate to "Chat" tab
# 2. Type: "What are the security issues?"
# 3. Press Enter or click Send
# 4. Verify:
#    - User message appears immediately
#    - Loading indicator appears
#    - Assistant response appears after LLM call

# Test 2: Test with issue context
# 1. Navigate to "Issues" tab
# 2. Click an issue
# 3. Navigate to "Chat" tab
# 4. Verify context banner shows issue ID
# 5. Type: "How do I fix this?"
# 6. Verify response is contextual

# Test 3: Test API calls
# Open Network tab
# Verify POST /chat includes:
# - {"message": "...", "context": null} (or issue ID)

# Test 4: Test conversation flow
# 1. Send message: "What's the most critical issue?"
# 2. Wait for response
# 3. Send follow-up: "How do I fix it?"
# 4. Verify conversation history maintained
# 5. Verify context from previous messages

# Test 5: Test error handling
# 1. Stop backend
# 2. Try to send message
# 3. Verify error message in chat

# Test 6: Visual QA checklist
# - [ ] User messages right-aligned (different color)
# - [ ] Assistant messages left-aligned with icon
# - [ ] Input disabled during loading
# - [ ] Smooth scroll animation to new messages
```

Expected results:
- Chat interface is responsive and intuitive
- Messages send successfully
- LLM responses are relevant and helpful
- Error states handled gracefully

### Risks & Mitigations
1. **Risk:** Slow LLM responses cause user frustration  
   **Mitigation:** Show typing indicator; set expectations with loading message

2. **Risk:** Context not passed correctly (wrong issue referenced)  
   **Mitigation:** Log context in API calls; display current context in UI

3. **Risk:** Message history grows too large (memory issues)  
   **Mitigation:** Limit to last 20 messages; implement clear history button

### Artifacts & Next Steps
**Keep:**
- `frontend/src/components/ChatPanel.jsx` with full implementation
- Updated API client with chat endpoint

**Next:** Proceed to Phase 12 for integration testing and LangSmith setup.

---

## Phase 12: Integration Testing & LangSmith Setup

### Goal / Outcome
Perform end-to-end integration testing of the complete system. Configure LangSmith for production observability. The result is a validated system with tracing enabled for debugging and monitoring.

### Deliverables
- [ ] LangSmith API key configured in backend
- [ ] LangSmith project created: "code-analyzer-capstone"
- [ ] Tracing enabled for all LangChain/LangGraph operations
- [ ] End-to-end test suite (full workflow)
- [ ] Integration test: upload project → analyze → view issues → chat
- [ ] Performance benchmarks (analysis time, API latency)
- [ ] LangSmith dashboard review (verify traces appear)
- [ ] Bug fixes from integration testing
- [ ] Test data: multiple sample projects with known issues

### Dependencies & Prerequisites
- Phases 1-11 completed (all components built)
- LangSmith account created (free tier available)
- LangSmith API key obtained from https://smith.langchain.com
- Test projects prepared with diverse issues

### Validation Criteria
- LangSmith traces appear in dashboard for all agent calls
- End-to-end workflow completes without errors
- All 3 specialist agents called for each file
- Issues persisted correctly to filesystem
- Frontend displays all analysis results
- Chat provides contextual answers
- Performance meets targets (< 10 sec per file)
- No memory leaks during extended testing

### Tests / Checks
```bash
# Test 1: Configure LangSmith
cat >> backend/.env << 'EOF'
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your-langsmith-api-key
LANGCHAIN_PROJECT=code-analyzer-capstone
EOF

# Test 2: Create diverse test projects
mkdir -p test_projects/security_focused
cat > test_projects/security_focused/auth.py << 'EOF'
import pickle
API_KEY = "hardcoded-secret-123"

def authenticate(user, pwd):
    return eval(f"check_{user}")  # Code injection

def load_session(data):
    return pickle.loads(data)  # Unsafe deserialization
EOF

mkdir -p test_projects/performance_focused
cat > test_projects/performance_focused/api.py << 'EOF'
def get_users():
    users = db.query("SELECT * FROM users")
    for user in users:
        # N+1 query
        posts = db.query(f"SELECT * FROM posts WHERE user_id={user.id}")
        user.posts = posts
    return users
EOF

# Test 3: Run end-to-end test
python tests/test_integration.py

# Test 4: Manual E2E test in browser
# 1. Start backend: cd backend && uvicorn app:app --reload
# 2. Start frontend: cd frontend && npm run dev
# 3. Complete full workflow:
#    a. Enter path: "./test_projects/security_focused"
#    b. Click "Start Analysis"
#    c. Wait for completion
#    d. Navigate to "Issues"
#    e. Verify issues appear
#    f. Click an issue
#    g. Verify detail displays
#    h. Navigate to "Chat"
#    i. Ask: "What are the security issues?"
#    j. Verify response mentions hardcoded secrets, code injection, etc.

# Test 5: Verify LangSmith traces
# 1. Open https://smith.langchain.com
# 2. Navigate to "code-analyzer-capstone" project
# 3. Verify recent traces:
#    - Manager agent calls
#    - Security analyst calls
#    - Performance analyst calls
#    - Architecture analyst calls
#    - Results compiler call
#    - Chat endpoint calls
# 4. Inspect a trace:
#    - View input/output
#    - Check token usage
#    - Verify no errors

# Test 6: Performance benchmarks
python -c "
import time
from agents.graph import create_analysis_graph, AnalysisState
from tools.code_tools import list_python_files

start = time.time()
graph = create_analysis_graph()
files = list_python_files('test_project_multi')
state = AnalysisState(
    target_path='test_project_multi',
    files_to_analyze=files,
    current_file='',
    issues=[],
    messages=[],
    scan_status='pending'
)
result = graph.invoke(state)
elapsed = time.time() - start
print(f'Analyzed {len(files)} files in {elapsed:.2f}s')
print(f'Average: {elapsed/len(files):.2f}s per file')
assert elapsed / len(files) < 10, 'Too slow!'
"

# Test 7: Memory leak check
# Run analysis 10 times and check memory usage
python -c "
import psutil
import os
from agents.graph import create_analysis_graph, AnalysisState
from tools.code_tools import list_python_files

process = psutil.Process(os.getpid())
graph = create_analysis_graph()
files = list_python_files('test_project_multi')

mem_start = process.memory_info().rss / 1024 / 1024  # MB
for i in range(10):
    state = AnalysisState(
        target_path='test_project_multi',
        files_to_analyze=files,
        current_file='',
        issues=[],
        messages=[],
        scan_status='pending'
    )
    result = graph.invoke(state)
mem_end = process.memory_info().rss / 1024 / 1024  # MB

print(f'Memory: {mem_start:.1f}MB -> {mem_end:.1f}MB')
assert mem_end - mem_start < 100, 'Memory leak detected!'
"
```

Expected results:
- LangSmith traces visible in dashboard
- E2E workflow completes successfully
- Performance within targets
- No errors in logs or console
- Memory stable across multiple runs

### Risks & Mitigations
1. **Risk:** LangSmith tracing increases latency  
   **Mitigation:** Test with/without tracing; tracing typically adds <50ms overhead

2. **Risk:** Integration tests flaky (timing issues)  
   **Mitigation:** Add explicit waits; use retry logic; mock slow components

3. **Risk:** Performance degrades with large codebases  
   **Mitigation:** Test with 100+ file project; implement file batching if needed

### Artifacts & Next Steps
**Keep:**
- Integration test suite in `tests/test_integration.py`
- Performance benchmark scripts
- LangSmith configuration in `.env`
- Test projects with diverse issues

**Next:** Proceed to Phase 13 for final validation and documentation.

---

## Phase 13: End-to-End Validation & Documentation

### Goal / Outcome
Perform final system validation, create comprehensive documentation, and prepare for demo/submission. The result is a production-ready system with complete documentation and demo materials.

### Deliverables
- [ ] Comprehensive README.md with setup instructions
- [ ] Architecture documentation with diagrams
- [ ] API documentation (OpenAPI/Swagger)
- [ ] User guide with screenshots
- [ ] Developer guide for extending the system
- [ ] Demo script and talking points
- [ ] Video walkthrough (5-10 minutes)
- [ ] Known limitations and future work documented
- [ ] All TODOs removed or documented
- [ ] Clean git history with meaningful commits
- [ ] Release checklist completed

### Dependencies & Prerequisites
- Phase 12 completed (integration testing done)
- All phases 1-11 completed and validated
- System running end-to-end successfully
- Screenshot tool and screen recorder ready

### Validation Criteria
- README includes all setup steps (environment, dependencies, API keys)
- User can follow README and get system running
- All API endpoints documented with examples
- User guide covers all major features
- Demo successfully showcases core value propositions
- Code is clean (no commented-out code, debug prints)
- Git repo is presentation-ready

### Tests / Checks
```bash
# Test 1: Verify README completeness
# README should cover:
# - [ ] Project overview and value proposition
# - [ ] Technology stack
# - [ ] Prerequisites
# - [ ] Installation steps
# - [ ] Environment variables
# - [ ] Running the application
# - [ ] Testing instructions
# - [ ] Troubleshooting common issues
# - [ ] Contributing guidelines (if applicable)

# Test 2: Fresh installation test
# 1. Clone repo to new location
# 2. Follow README step-by-step
# 3. Verify system runs without issues
# 4. Document any steps that fail

# Test 3: API documentation review
curl http://localhost:8000/docs  # FastAPI auto-docs
# Verify all endpoints documented with:
# - Description
# - Request body schema
# - Response schema
# - Example requests/responses

# Test 4: Create demo script
cat > DEMO.md << 'EOF'
# Demo Script

## Setup (2 min)
1. Start backend: `cd backend && uvicorn app:app`
2. Start frontend: `cd frontend && npm run dev`
3. Open browser to http://localhost:5173

## Demo Flow (5 min)
1. **Analysis Dashboard** (2 min)
   - Show path input
   - Trigger analysis on sample project
   - Highlight real-time progress (if implemented)
   - Point out issue counts by category

2. **Issues List** (2 min)
   - Show filtering by type/risk
   - Click through different issues
   - Highlight markdown rendering
   - Show issue location and code snippet

3. **Chat Interface** (1 min)
   - Ask: "What's the most critical issue?"
   - Ask follow-up: "How do I fix the SQL injection?"
   - Show contextual understanding

## Key Points
- Multi-agent architecture (Security, Performance, Architecture)
- LangGraph orchestration
- Persistent issue tracking
- Interactive exploration via chat
- Extensible to other languages/tools
EOF

# Test 5: Record demo video
# Use screen recording tool (OBS, QuickTime, etc.)
# Record 5-10 minute walkthrough following demo script

# Test 6: Code cleanup
# Remove debug statements
grep -r "print(" backend/  # Should only show intentional logging
grep -r "console.log" frontend/src/  # Should be minimal

# Remove commented code
# Review all files for TODO comments
grep -r "TODO" backend/ frontend/  # Document remaining TODOs in issues

# Test 7: Git hygiene
git log --oneline  # Review commit messages
# Verify:
# - Meaningful commit messages
# - Logical commit grouping
# - No sensitive data (API keys) in history

# Test 8: Final validation checklist
# Complete system test:
# - [ ] Backend starts without errors
# - [ ] Frontend starts without errors
# - [ ] Analysis completes successfully
# - [ ] Issues display correctly
# - [ ] Chat responds appropriately
# - [ ] LangSmith traces appear
# - [ ] No console errors
# - [ ] Performance acceptable
# - [ ] Documentation complete
# - [ ] Demo ready
```

Expected results:
- Complete, professional documentation
- System validated end-to-end
- Demo materials ready
- Code clean and well-organized
- Project ready for submission/presentation

### Risks & Mitigations
1. **Risk:** Documentation out of sync with code  
   **Mitigation:** Review docs after any code changes; include version numbers

2. **Risk:** Demo fails during presentation  
   **Mitigation:** Record backup video; test demo multiple times; have troubleshooting guide

3. **Risk:** Unclear value proposition  
   **Mitigation:** Lead with concrete examples; show actual security issues found

### Artifacts & Next Steps
**Keep:**
- Complete documentation set
- Demo video and script
- Clean, release-ready codebase
- Presentation materials

**Next:** System is complete and ready for demo/submission!

---

## Clarifying Questions

Before proceeding with implementation, please confirm or clarify the following assumptions:

1. **LLM Choice:** Will you use Ollama (local, free) or OpenAI API (cloud, paid)? This affects setup instructions and cost considerations. Recommendation: Start with Ollama for development, add OpenAI support for production.

2. **Frontend Hosting:** Is the frontend expected to run only locally (Vite dev server) or do you need production build instructions (deployment to Vercel, Netlify, etc.)?

3. **WebSocket Implementation:** The original plan mentions WebSocket for real-time progress. Should this be prioritized (more complex but better UX) or is basic polling acceptable (simpler, good enough for MVP)?

4. **LangSmith Access:** Do you have a LangSmith account and API key, or should setup instructions assume this is optional? (It's very useful for debugging but not strictly required.)

5. **Multi-language Support:** The MVP focuses on Python code analysis. Should the architecture be designed to easily add JavaScript/TypeScript analysis later, or is Python-only sufficient for now?

---

## Appendix: Parallel Work Opportunities

The following phases can be worked on in parallel after their dependencies are met:

**Backend Track (Sequential):**
- Phase 1 → 2 → 3 → 4 → 5 → 6 → 7

**Frontend Track (Can start after Phase 7):**
- Phase 8 → 9 (depends on Phase 7 API)
- Phase 10 (depends on Phase 7 API)
- Phase 11 (depends on Phase 7 API)

**Integration Track:**
- Phase 12 (depends on Phases 1-11)
- Phase 13 (depends on Phase 12)

**Optimal Workflow:**
1. Complete backend phases 1-7 first (this is the critical path)
2. Start frontend phases 8-11 in parallel (can be done by different developer)
3. Integrate and test in phases 12-13

Total estimated time with parallel work: Backend track + Integration (vs. all sequential which would be longer).
