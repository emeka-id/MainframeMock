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
    legal_name: str
    location: str
    preferred_account_type: str
    status: str
    is_flagged: bool
    created_utc: str
    last_updated_utc: str


@dataclass
class Account:
    account_id: str
    customer_id: str
    account_type: str
    balance: str
    total_assets: str
    status: str


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

    def create_customer(
        self,
        name: str,
        *,
        legal_name: str = "",
        location: str = "",
        preferred_account_type: str = "",
    ) -> Customer:
        if not name.strip():
            raise ValueError("Customer name is required")
        if preferred_account_type:
            preferred_account_type = self._validate_account_type(preferred_account_type)
        now = self._now()
        customer = Customer(
            customer_id=self._new_customer_id(),
            name=name.strip(),
            legal_name=legal_name.strip(),
            location=location.strip(),
            preferred_account_type=preferred_account_type,
            status="active",
            is_flagged=False,
            created_utc=now,
            last_updated_utc=now,
        )
        self.state["customers"][customer.customer_id] = asdict(customer)
        self._save()
        return customer

    def _validate_account_type(self, account_type: str) -> str:
        normalized_type = account_type.strip().lower()
        if normalized_type not in {"corporate", "individual"}:
            raise ValueError("Account type must be corporate or individual")
        return normalized_type

    def _get_customer_data(self, customer_id: str) -> Dict:
        customer = self.state["customers"].get(customer_id)
        if not customer:
            raise ValueError("Customer does not exist")
        customer.setdefault("legal_name", "")
        customer.setdefault("location", "")
        customer.setdefault("preferred_account_type", "")
        customer.setdefault("status", "active")
        customer.setdefault("is_flagged", False)
        customer.setdefault("created_utc", self._now())
        customer.setdefault("last_updated_utc", customer["created_utc"])
        return customer

    def _assert_customer_active(self, customer_id: str) -> None:
        customer = self._get_customer_data(customer_id)
        if customer["status"] == "deleted":
            raise ValueError("Customer is deleted")
        if customer["status"] == "frozen":
            raise ValueError("Customer is frozen")

    def update_customer(
        self,
        customer_id: str,
        *,
        name: str | None = None,
        legal_name: str | None = None,
        location: str | None = None,
        preferred_account_type: str | None = None,
    ) -> Customer:
        customer = self._get_customer_data(customer_id)
        if customer["status"] == "deleted":
            raise ValueError("Deleted customer records cannot be updated")
        if name is not None:
            if not name.strip():
                raise ValueError("Customer name is required")
            customer["name"] = name.strip()
        if legal_name is not None:
            customer["legal_name"] = legal_name.strip()
        if location is not None:
            customer["location"] = location.strip()
        if preferred_account_type is not None:
            customer["preferred_account_type"] = self._validate_account_type(preferred_account_type)
        customer["last_updated_utc"] = self._now()
        self._save()
        return Customer(**customer)

    def freeze_customer(self, customer_id: str) -> Customer:
        customer = self._get_customer_data(customer_id)
        if customer["status"] == "deleted":
            raise ValueError("Deleted customer cannot be frozen")
        customer["status"] = "frozen"
        customer["last_updated_utc"] = self._now()
        for account in self.state["accounts"].values():
            if account["customer_id"] == customer_id and account.get("status", "open") != "closed":
                account["status"] = "frozen"
        self._save()
        return Customer(**customer)

    def flag_customer(self, customer_id: str, flagged: bool = True) -> Customer:
        customer = self._get_customer_data(customer_id)
        if customer["status"] == "deleted":
            raise ValueError("Deleted customer cannot be flagged")
        customer["is_flagged"] = bool(flagged)
        customer["last_updated_utc"] = self._now()
        self._save()
        return Customer(**customer)

    def delete_customer(self, customer_id: str) -> Customer:
        customer = self._get_customer_data(customer_id)
        customer["status"] = "deleted"
        customer["last_updated_utc"] = self._now()
        for account in self.state["accounts"].values():
            if account["customer_id"] == customer_id:
                account["status"] = "closed"
        self._save()
        return Customer(**customer)

    def get_customer_status(self, customer_id: str) -> Dict[str, str | int | bool]:
        customer = self._get_customer_data(customer_id)
        accounts = self.customer_accounts(customer_id)
        total_assets = sum(Decimal(account.balance) for account in accounts)
        open_accounts = sum(1 for account in accounts if account.status not in {"closed"})
        return {
            "customer_id": customer_id,
            "status": customer["status"],
            "is_flagged": bool(customer["is_flagged"]),
            "account_count": len(accounts),
            "open_accounts": open_accounts,
            "total_assets": f"{total_assets:.2f}",
        }

    def open_account(self, customer_id: str, account_type: str = "") -> Account:
        self._assert_customer_active(customer_id)
        customer = self._get_customer_data(customer_id)
        requested_type = account_type or customer.get("preferred_account_type", "")
        normalized_type = self._validate_account_type(requested_type)
        account = Account(
            account_id=self._new_account_id(),
            customer_id=customer_id,
            account_type=normalized_type,
            balance="0.00",
            total_assets="0.00",
            status="open",
        )
        self.state["accounts"][account.account_id] = asdict(account)
        self._save()
        return account

    def get_account(self, account_id: str) -> Account:
        data = self.state["accounts"].get(account_id)
        if not data:
            raise ValueError("Account does not exist")
        data.setdefault("total_assets", data.get("balance", "0.00"))
        data.setdefault("status", "open")
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
        if account.status != "open":
            raise ValueError("Account is not open for transactions")
        self._assert_customer_active(account.customer_id)
        current = Decimal(account.balance)
        updated = current + amt
        self.state["accounts"][account_id]["balance"] = f"{updated:.2f}"
        self.state["accounts"][account_id]["total_assets"] = f"{updated:.2f}"
        tx = self._record_tx(account_id, "DEPOSIT", amt, note)
        self._save()
        return tx

    def withdraw(self, account_id: str, amount: str | int | float | Decimal, note: str = "") -> Transaction:
        amt = _money(amount)
        if amt == Decimal("0.00"):
            raise ValueError("Withdrawal must be greater than zero")
        account = self.get_account(account_id)
        if account.status != "open":
            raise ValueError("Account is not open for transactions")
        self._assert_customer_active(account.customer_id)
        current = Decimal(account.balance)
        if amt > current:
            raise ValueError("Insufficient funds")
        updated = current - amt
        self.state["accounts"][account_id]["balance"] = f"{updated:.2f}"
        self.state["accounts"][account_id]["total_assets"] = f"{updated:.2f}"
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
            account.setdefault("status", "open")
            account.setdefault("total_assets", account.get("balance", "0.00"))
            tx_count = sum(1 for tx in self.state["transactions"] if tx["account_id"] == account_id)
            lines.append(
                f"{account_id} | {account['account_type'].upper():8} | "
                f"BAL ${account['balance']:>10} | ASSETS ${account['total_assets']:>10} | "
                f"STATUS {account['status'].upper():>6} | TX {tx_count:>4}"
            )
        return "\n".join(lines)
