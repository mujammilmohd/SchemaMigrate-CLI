# SchemaMigrate CLI

**A Python-based command-line tool for managing database schema migrations using JSON files.**

## About the Project

SchemaMigrate CLI is a tool that helps developers manage database schema changes safely and systematically.

It allows users to create migration files, apply pending migrations, check migration history, and roll back the latest migration.

This project is developed as part of our OJT (On-the-Job Training) at Polaris School of Technology.

## Features

- **Create Migration:** Create new migration files.
- **Apply Migration:** Apply pending migrations in the correct order.
- **Migration History:** Track previously applied migrations.
- **Rollback:** Reverse the latest migration.
- **Status:** Check the current migration status.
- **Validation:** Detect invalid JSON files and unsupported operations.
- **JSON Storage:** Store database information locally using JSON files.

## Technologies Used

- Python 3
- JSON
- Python Standard Libraries
- Git & GitHub

## Project Structure

```text
SchemaMigrate/
│
├── main.py
├── patches/
├── database/
│   └── db.json
├── src/
├── tests/
├── sample-data/
├── README.md
└── .gitignore
```

## Getting Started

### 1. Clone the Repository

```bash
git clone YOUR_REPOSITORY_URL
```

### 2. Open the Project

```bash
cd SchemaMigrate
```

### 3. Run the Project

```bash
python main.py
```

## Team Members
| Mujammil | Developer |
| Nikita   | Developer |

## Project Information

- **Project Name:** SchemaMigrate CLI
- **Project ID:** PST_PD_176
- **Institution:** Polaris School of Technology
- **Project Type:** OJT Project
- **Language:** Python

## Learning Outcomes

Through this project, we aim to improve our understanding of Python, file handling, JSON operations, command-line interfaces, error handling, and software development using Git and GitHub.

---

**Developed with Python by Mujammil and Nikita.**
