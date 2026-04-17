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
6) End of day report
7) Exit
"""

    while True:
        print(menu)
        choice = input("Select option: ").strip()

        try:
            if choice == "1":
                name = input("Customer name: ")
                customer = bank.create_customer(name)
                print(f"Created customer {customer.customer_id} ({customer.name})")
            elif choice == "2":
                customer_id = input("Customer ID: ").strip()
                account_type = input("Account type [checking/savings]: ")
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
                print(bank.end_of_day_report())
            elif choice == "7":
                print("Session complete.")
                break
            else:
                print("Unknown option.")
        except ValueError as exc:
            print(f"ERROR: {exc}")


if __name__ == "__main__":
    main()
