Projet 2A 2025 — EnsaiGPT
<br>
Development environment
<br>
Quick summary
<br>
Python is a widely used scripting language, especially in data science, but its developer experience (DX) can be chaotic due to:
<br>
multiple Python versions coexisting on the same machine
inconsistent interpreter selection across tools
global package installations causing version conflicts
<br>
To avoid these issues, each project should have its own isolated environment.
This project uses PDM, which provides exactly that.
<br>
Package manager for the project
<br>
We use PDM because it allows:
<br>
declaring dependencies in pyproject.toml
locking versions in pdm.lock
automatically creating an isolated virtual environment
defining scripts and configuration in a single file
<br>
Formatter and linter
<br>
Instead of the classical trio flake8 + black + isort, this project uses Ruff, a fast Rust-based tool that performs:
<br>
linting
formatting
import sorting
<br>
Type checking
<br>
Type checking is optional but recommended.
If types are added, MyPy will validate them:
<br>
pdm typecheck
<br>
How to use
<br>
1. Install PDM
<br>
Install PDM globally:
<br>
pip install --user pdm
<br>
2. Install the project
<br>
Inside the project folder:
<br>
pdm install
<br>
This installs all dependencies inside an isolated virtual environment.
<br>
3. Environment setup
<br>
Before running the application:
<br>
Create a .env file based on .env.example
Fill in database and API keys as required
<br>
4. Initialize the PostgreSQL database
<br>
Initialize the PostgreSQL database using either:
<br>
data/init_db.sql
src/Database/init_db.py
<br>
5. Run the project
<br>
pdm run python src/main.py
<br>
This ensures the correct interpreter and dependencies are used.
<br>
6. Adding and removing dependencies
<br>
Add:
pdm add my-package
<br>
Remove:
pdm remove my-package
<br>
7. Formatter, linter, and type-checker
<br>
Format:
pdm format
<br>
Lint:
pdm lint
<br>
Fix:
pdm lint --fix
<br>
Type check:
pdm typecheck
<br>
Project Structure
<br>
(identique, affichage inchangé)
<br>
Features
<br>
EnsaiGPT provides:
<br>
User management
Conversation creation and management
Collaboration handling
Messaging system
External LLM integration
Statistics
TXT export
Feedback management
Search features
Interactive CLI
PostgreSQL support
Unit + integration tests
<br>
Additional notes and requirements
<br>
Packaging the app
<br>
This project is not meant to be packaged (distribution = false).
Use GitHub’s “Download ZIP” feature.
<br>
For grading
<br>
pdm install
pdm run python src/main.py
<br>
Recommended libraries
<br>
requests
FastAPI / Uvicorn
psycopg2
pytest
<br>
Recommended VSCode extensions
<br>
Listed in extensions.txt.
Disable overlapping linters (flake8, pylance…).
<br>