from __future__ import annotations

from bank_system.core import BankSystem


def main() -> None:
    bank = BankSystem()

    menu = """
MAINFRAME BANK MENU
-------------------
1) Create customer
2) Open account
3) Deposit
4) Withdraw
5) Transfer
6) Update customer
7) Freeze customer
8) Flag customer
9) Delete customer
10) Customer status
11) End of day report
12) Exit
"""

    while True:
        print(menu)
        choice = input("Select option: ").strip()

        try:
            if choice == "1":
                name = input("Customer name: ")
                legal_name = input("Legal name (optional): ")
                location = input("Location (optional): ")
                preferred = input("Default account type [checking/savings] (optional): ")
                customer = bank.create_customer(
                    name,
                    legal_name=legal_name,
                    location=location,
                    preferred_account_type=preferred,
                )
                print(f"Created customer {customer.customer_id} ({customer.name})")
            elif choice == "2":
                customer_id = input("Customer ID: ").strip()
                account_type = input("Account type [checking/savings] (blank uses customer default): ")
                account = bank.open_account(customer_id, account_type)
                print(f"Opened account {account.account_id} for {account.customer_id}")
            elif choice == "3":
                account_id = input("Account ID: ").strip()
                amount = input("Amount: ").strip()
                tx = bank.deposit(account_id, amount)
                print(f"Deposit posted: {tx.transaction_id}")
            elif choice == "4":
                account_id = input("Account ID: ").strip()
                amount = input("Amount: ").strip()
                tx = bank.withdraw(account_id, amount)
                print(f"Withdrawal posted: {tx.transaction_id}")
            elif choice == "5":
                from_account = input("From account: ").strip()
                to_account = input("To account: ").strip()
                amount = input("Amount: ").strip()
                debit, credit = bank.transfer(from_account, to_account, amount)
                print(f"Transfer posted: {debit.transaction_id} / {credit.transaction_id}")
            elif choice == "6":
                customer_id = input("Customer ID: ").strip()
                name = input("Updated display name (optional): ").strip() or None
                legal_name = input("Updated legal name (optional): ").strip() or None
                location = input("Updated location (optional): ").strip() or None
                preferred = input("Updated default account type [checking/savings] (optional): ").strip() or None
                customer = bank.update_customer(
                    customer_id,
                    name=name,
                    legal_name=legal_name,
                    location=location,
                    preferred_account_type=preferred,
                )
                print(f"Customer updated: {customer.customer_id}")
            elif choice == "7":
                customer_id = input("Customer ID: ").strip()
                customer = bank.freeze_customer(customer_id)
                print(f"Customer frozen: {customer.customer_id}")
            elif choice == "8":
                customer_id = input("Customer ID: ").strip()
                is_flagged = input("Flag customer? [y/n]: ").strip().lower() in {"y", "yes", "1", "true"}
                customer = bank.flag_customer(customer_id, is_flagged)
                print(f"Customer flag updated: {customer.customer_id} -> {customer.is_flagged}")
            elif choice == "9":
                customer_id = input("Customer ID: ").strip()
                customer = bank.delete_customer(customer_id)
                print(f"Customer deleted: {customer.customer_id}")
            elif choice == "10":
                customer_id = input("Customer ID: ").strip()
                status = bank.get_customer_status(customer_id)
                print(
                    f"{status['customer_id']} | STATUS {status['status'].upper()} | "
                    f"FLAGGED {status['is_flagged']} | ACCOUNTS {status['account_count']} | "
                    f"OPEN {status['open_accounts']} | TOTAL ASSETS ${status['total_assets']}"
                )
            elif choice == "11":
                print(bank.end_of_day_report())
            elif choice == "12":
                print("Session complete.")
                break
            else:
                print("Unknown option.")
        except ValueError as exc:
            print(f"ERROR: {exc}")


if __name__ == "__main__":
    main()
