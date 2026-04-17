# Mainframe Bank System

A lightweight, local "mainframe-style" banking system implemented in Python.

## Features

- Customer onboarding
- Open checking or savings accounts
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
