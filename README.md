# Project 2A 2025 — EnsaiGPT

---

## Quick Overview

**EnsaiGPT** is a Python project designed to offer an optimal and isolated development experience using PDM.  
The project aims to solve the main issues encountered in data science, such as:
- Multiple Python versions coexisting
- Inconsistent interpreter selection across tools
- Version conflicts related to global packages

Each project therefore has its own virtual environment, ensuring stability and reproducibility.

---

## Development Environment

- **Package Manager: [PDM](https://pdm.fming.dev/)**
  - Dependency declaration via `pyproject.toml`
  - Versions locked in `pdm.lock`
  - Automatic creation of an isolated virtual environment
  - Centralized configuration

- **Formatting & Linting: [Ruff](https://github.com/astral-sh/ruff)**
  - Ultra-fast formatting, linting, and import sorting thanks to Rust
  - Replaces the classics: `flake8`, `black`, `isort`

- **Type Checking: [MyPy](http://mypy-lang.org/)**
  - Optional but strongly recommended.
  - Use via:  
    ```
    pdm typecheck
    ```

---

## How to Use the Project?

1. **Install PDM**
   ```bash
   pip install --user pdm
   ```

2. **Install Dependencies**
   ```bash
   pdm install
   ```
   > Installs all dependencies in the project’s isolated virtual environment.

3. **Configure the Environment**
   - Copy `.env.example` to `.env` or use 
   ```bash
   cp .env.example .env
   ```

4. **Initialize the PostgreSQL Database**
   - Or via the Python script: `src/Database/init_db.py`

5. **Run the Application**
   ```bash
   pdm run python src/main.py
   ```

6. **Manage Dependencies**
   - **Add:**  
     ```bash
     pdm add package-name
     ```
   - **Remove:**  
     ```bash
     pdm remove package-name
     ```

7. **Quality Tools**
   - **Format:**  
     ```bash
     pdm format
     ```
   - **Lint:**  
     ```bash
     pdm lint
     ```
   - **Auto-correct:**  
     ```bash
     pdm lint --fix
     ```
   - **Type checking:**  
     ```bash
     pdm typecheck
     ```

---

## Project Structure

├── README.md
├── README.students.md
├── ARCHITECTURE.md
├── CONTRIBUTING.md
├── LICENSE
├── pyproject.toml
├── pdm.lock
├── requirements.txt
├── .env.example
├── .coveragerc
├── pytest.ini
├── extensions.txt
├── data/
│   └── init_db.sql
├── doc/
│   └── suivi/
│       ├── 2025.09.04-semaine1.md
│       ├── 2025.09.11-semaine2.md
│       ├── 2025.09.16-semaine3.md
│       ├── 2025.09.25-semaine4.md
│       ├── 2025.10.02-semaine5.md
│       ├── 2025.10.09-semaine6.md
│       ├── 2025.10.16-semaine7.md
│       ├── 2025.10.23-semaine8.md
│       ├── 2025.11.06-semaine10.md
│       └── 2025.11.13-semaine11.md
├── exports/
│   ├── discussion de colluche.txt
│   └── Gros dab.txt
├── src/
│   ├── main.py
│   ├── Service/
│   │   ├── AuthService.py
│   │   ├── CollaborationService.py
│   │   ├── ConversationService.py
│   │   ├── ExportService.py
│   │   ├── FeedbackService.py
│   │   ├── LLMService.py
│   │   ├── MessageService.py
│   │   ├── SearchService.py
│   │   └── UserService.py
│   ├── DAO/
│   │   ├── DBConnector.py
│   │   ├── ConversationDAO.py
│   │   ├── MessageDAO.py
│   │   ├── FeedbackDAO.py
│   │   ├── UserDAO.py
│   │   └── CollaborationDAO.py
│   ├── ObjetMetier/
│   │   ├── User.py
│   │   ├── Conversation.py
│   │   ├── Message.py
│   │   ├── Feedback.py
│   │   └── Collaboration.py
│   ├── Database/
│   │   ├── init_db.py
│   │   ├── manage_test_db.py
│   │   ├── schema_sql.py
│   │   └── settings.py
│   ├── cli/
│   │   ├── ui.py
│   │   ├── context.py
│   │   └── pages/
│   │       ├── auth.py
│   │       ├── home.py
│   │       ├── user.py
│   │       ├── conversations.py
│   │       ├── conversation_detail.py
│   │       ├── collaboration.py
│   │       ├── invitee.py
│   │       └── feedback.py
│   ├── tests/
│   │   ├── test_db_infra.py
│   │   ├── test_dao/
│   │   ├── test_ObjetMetier/
│   │   └── test_Database/
│   └── Utils/
│       ├── Singleton.py
│       └── log_decorator.py
└── .vscode/
    └── settings.json

---

## Main Features

- User management
- Creation & management of conversations
- Multi-user collaboration
- Messaging system
- External LLM integration
- Statistics
- TXT export
- Feedback management
- Search features
- Interactive CLI
- PostgreSQL support
- Unit & integration tests

---
