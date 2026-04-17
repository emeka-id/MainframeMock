from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
import json
from typing import Dict, List

CENT = Decimal("0.01")


def _money(amount: str | int | float | Decimal) -> Decimal:
    value = Decimal(str(amount)).quantize(CENT, rounding=ROUND_HALF_UP)
    if value < Decimal("0.00"):
        raise ValueError("Amount cannot be negative")
    return value


@dataclass
class Customer:
    customer_id: str
    name: str


@dataclass
class Account:
    account_id: str
    customer_id: str
    account_type: str
    balance: str


@dataclass
class Transaction:
    transaction_id: str
    account_id: str
    tx_type: str
    amount: str
    timestamp_utc: str
    note: str = ""


class BankSystem:
    def __init__(self, db_path: str = "data/mainframe_bank.json") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.state = self._load()

    def _load(self) -> Dict:
        if self.db_path.exists():
            with self.db_path.open("r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "next_customer": 100000,
            "next_account": 700000,
            "next_tx": 1,
            "customers": {},
            "accounts": {},
            "transactions": [],
        }

    def _save(self) -> None:
        with self.db_path.open("w", encoding="utf-8") as f:
            json.dump(self.state, f, indent=2, sort_keys=True)

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _new_customer_id(self) -> str:
        cid = f"C{self.state['next_customer']}"
        self.state["next_customer"] += 1
        return cid

    def _new_account_id(self) -> str:
        aid = f"A{self.state['next_account']}"
        self.state["next_account"] += 1
        return aid

    def _new_tx_id(self) -> str:
        tid = f"T{self.state['next_tx']:09d}"
        self.state["next_tx"] += 1
        return tid

    def create_customer(self, name: str) -> Customer:
        if not name.strip():
            raise ValueError("Customer name is required")
        customer = Customer(customer_id=self._new_customer_id(), name=name.strip())
        self.state["customers"][customer.customer_id] = asdict(customer)
        self._save()
        return customer

    def open_account(self, customer_id: str, account_type: str) -> Account:
        if customer_id not in self.state["customers"]:
            raise ValueError("Customer does not exist")
        normalized_type = account_type.strip().lower()
        if normalized_type not in {"checking", "savings"}:
            raise ValueError("Account type must be checking or savings")
        account = Account(
            account_id=self._new_account_id(),
            customer_id=customer_id,
            account_type=normalized_type,
            balance="0.00",
        )
        self.state["accounts"][account.account_id] = asdict(account)
        self._save()
        return account

    def get_account(self, account_id: str) -> Account:
        data = self.state["accounts"].get(account_id)
        if not data:
            raise ValueError("Account does not exist")
        return Account(**data)

    def _record_tx(self, account_id: str, tx_type: str, amount: Decimal, note: str = "") -> Transaction:
        tx = Transaction(
            transaction_id=self._new_tx_id(),
            account_id=account_id,
            tx_type=tx_type,
            amount=f"{amount:.2f}",
            timestamp_utc=self._now(),
            note=note,
        )
        self.state["transactions"].append(asdict(tx))
        return tx

    def deposit(self, account_id: str, amount: str | int | float | Decimal, note: str = "") -> Transaction:
        amt = _money(amount)
        if amt == Decimal("0.00"):
            raise ValueError("Deposit must be greater than zero")
        account = self.get_account(account_id)
        current = Decimal(account.balance)
        updated = current + amt
        self.state["accounts"][account_id]["balance"] = f"{updated:.2f}"
        tx = self._record_tx(account_id, "DEPOSIT", amt, note)
        self._save()
        return tx

    def withdraw(self, account_id: str, amount: str | int | float | Decimal, note: str = "") -> Transaction:
        amt = _money(amount)
        if amt == Decimal("0.00"):
            raise ValueError("Withdrawal must be greater than zero")
        account = self.get_account(account_id)
        current = Decimal(account.balance)
        if amt > current:
            raise ValueError("Insufficient funds")
        updated = current - amt
        self.state["accounts"][account_id]["balance"] = f"{updated:.2f}"
        tx = self._record_tx(account_id, "WITHDRAWAL", amt, note)
        self._save()
        return tx

    def transfer(self, from_account: str, to_account: str, amount: str | int | float | Decimal) -> List[Transaction]:
        if from_account == to_account:
            raise ValueError("Cannot transfer to the same account")
        amt = _money(amount)
        if amt == Decimal("0.00"):
            raise ValueError("Transfer amount must be greater than zero")

        self.withdraw(from_account, amt, note=f"TRANSFER TO {to_account}")
        credit_tx = self.deposit(to_account, amt, note=f"TRANSFER FROM {from_account}")
        debit_tx = Transaction(**self.state["transactions"][-2])
        self._save()
        return [debit_tx, credit_tx]

    def customer_accounts(self, customer_id: str) -> List[Account]:
        accounts = []
        for data in self.state["accounts"].values():
            if data["customer_id"] == customer_id:
                accounts.append(Account(**data))
        return sorted(accounts, key=lambda a: a.account_id)

    def end_of_day_report(self) -> str:
        lines = ["MAINFRAME BANK - END OF DAY REPORT", "=" * 40]
        for account_id in sorted(self.state["accounts"].keys()):
            account = self.state["accounts"][account_id]
            tx_count = sum(1 for tx in self.state["transactions"] if tx["account_id"] == account_id)
            lines.append(
                f"{account_id} | {account['account_type'].upper():8} | BAL ${account['balance']:>10} | TX {tx_count:>4}"
            )
        return "\n".join(lines)
