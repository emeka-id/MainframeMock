# Mainframe Bank System

A lightweight, local "mainframe-style" banking system implemented in Python.

## Features

- Customer onboarding
- Customer profile capture (legal name, location, preferred account type)
- Customer lifecycle actions (update, freeze, flag, delete)
- Customer status lookup including total assets
- Open corporate or individual accounts
- Deposit and withdraw funds
- Transfer between accounts
- Transaction journal (append-only)
- End-of-day batch report by account

The command-line interface intentionally uses panel-style prompts to mimic old terminal workflows.

## Quick start

```bash
python3 -m bank_system.cli
```

## Data

By default, data is stored in `data/mainframe_bank.json`.

## Run tests

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```

## Package for RPA export

If you want an RPA tool (UiPath, Automation Anywhere, Power Automate Desktop, etc.)
to run this system as a standalone executable, package it with PyInstaller.

1. Create a virtual environment and install build dependencies:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install pyinstaller
   ```

2. Build a single-file executable for the CLI:

   ```bash
   pyinstaller --onefile --name mainframe-bank bank_system/cli.py
   ```

3. Export the artifacts your RPA job needs:
   - Executable: `dist/mainframe-bank`
   - Data file (optional seed/state): `data/mainframe_bank.json`

4. In your RPA workflow:
   - Use a "Start Process"/"Run" activity to launch `mainframe-bank`.
   - Send menu selections and text input through stdin/keystrokes.
   - Capture stdout to parse IDs (customer/account/transaction) and statuses.

### Non-interactive automation option

For more reliable bots, prefer calling `BankSystem` directly from a thin Python
wrapper (instead of menu keystrokes), then package that wrapper with
PyInstaller. This avoids fragile prompt timing and screen-scraping.

Example wrapper pattern:

```python
from bank_system.core import BankSystem

bank = BankSystem(db_path="data/mainframe_bank.json")
customer = bank.create_customer("RPA Customer")
account = bank.open_account(customer.customer_id, "corporate")
bank.deposit(account.account_id, "100.00")
```
