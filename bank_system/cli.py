from __future__ import annotations

import time

from bank_system.core import BankSystem


MENU_DELAY_SECONDS = 0.35
TRANSACTION_DELAY_SECONDS = 0.55

ERROR_CODES = {
    "Customer does not exist": "MBE-104",
    "Customer is deleted": "MBE-105",
    "Customer is frozen": "MBE-106",
    "Deleted customer records cannot be updated": "MBE-107",
    "Deleted customer cannot be frozen": "MBE-108",
    "Deleted customer cannot be flagged": "MBE-109",
    "Customer name is required": "MBE-110",
    "Account does not exist": "MBE-201",
    "Account type must be checking or savings": "MBE-202",
    "Account is not open for transactions": "MBE-203",
    "Amount cannot be negative": "MBE-204",
    "Deposit must be greater than zero": "MBE-205",
    "Withdrawal must be greater than zero": "MBE-206",
    "Transfer amount must be greater than zero": "MBE-207",
    "Cannot transfer to the same account": "MBE-208",
    "Insufficient funds": "MBE-209",
}


def clear_screen() -> None:
    print("\033[2J\033[H", end="")


def draw_screen(title: str, lines: list[str] | None = None, footer: str = "PF1=HELP  PF3=EXIT") -> None:
    lines = lines or []
    width = 78
    border = "+" + ("-" * width) + "+"
    clear_screen()
    print(border)
    print(f"|{title.center(width)}|")
    print(border)
    for line in lines:
        print(f"| {line[: width - 2].ljust(width - 2)}|")
    print(border)
    print(f"| {footer.ljust(width - 1)}|")
    print(border)


def show_help() -> None:
    draw_screen(
        "PF1 HELP - OPERATOR KEYS",
        [
            "PF1 -> open this help panel",
            "PF3 -> cancel current screen / return to previous menu",
            "Use numeric options from the main menu to drive workflows",
            "All errors include MBE error code for Blue Prism branch handling",
        ],
        footer="Press ENTER to return",
    )
    input()


def read_field(prompt: str) -> str:
    value = input(prompt).strip()
    if value.upper() == "PF1":
        show_help()
        return read_field(prompt)
    return value


def pause(seconds: float = MENU_DELAY_SECONDS) -> None:
    time.sleep(seconds)


def render_error(exc: ValueError) -> None:
    message = str(exc)
    code = ERROR_CODES.get(message, "MBE-999")
    draw_screen(
        "MAINFRAME ERROR PANEL",
        [f"ERROR CODE: {code}", f"MESSAGE   : {message}", "", "Action: verify request data and retry."],
        footer="Press ENTER to continue",
    )
    input()


def transaction_confirmation(action: str, tx_ids: str, detail_lines: list[str]) -> None:
    draw_screen(
        "TRANSACTION CONFIRMATION",
        [f"ACTION : {action}", f"TX-ID  : {tx_ids}"] + detail_lines + ["", "STATUS : POSTED"],
        footer="Press ENTER to continue",
    )
    time.sleep(TRANSACTION_DELAY_SECONDS)
    input()


def lookup_account_screen(bank: BankSystem) -> None:
    draw_screen("ACCOUNT LOOKUP")
    account_id = read_field("Account ID (or PF3): ")
    if account_id.upper() == "PF3":
        return
    account = bank.get_account(account_id)
    draw_screen(
        "ACCOUNT LOOKUP RESULT",
        [
            f"ACCOUNT ID : {account.account_id}",
            f"CUSTOMER   : {account.customer_id}",
            f"TYPE       : {account.account_type.upper()}",
            f"BALANCE    : ${account.balance}",
            f"ASSETS     : ${account.total_assets}",
            f"STATUS     : {account.status.upper()}",
        ],
        footer="Press ENTER to continue",
    )
    input()


def main() -> None:
    bank = BankSystem()

    while True:
        draw_screen(
            "MAINFRAME BANK MENU",
            [
                "1) Create customer",
                "2) Open account",
                "3) Deposit",
                "4) Withdraw",
                "5) Transfer",
                "6) Update customer",
                "7) Freeze customer",
                "8) Flag customer",
                "9) Delete customer",
                "10) Customer status",
                "11) End of day report",
                "12) Account lookup",
                "13) Exit",
            ],
            footer="PF1=HELP  PF3=EXIT  Select option and press ENTER",
        )
        choice = read_field("Select option: ")
        if choice.upper() == "PF3":
            choice = "13"
        if choice.upper() == "PF1":
            show_help()
            continue

        try:
            if choice == "1":
                draw_screen("CREATE CUSTOMER")
                name = read_field("Customer name (or PF3): ")
                if name.upper() == "PF3":
                    continue
                legal_name = read_field("Legal name (optional): ")
                location = read_field("Location (optional): ")
                preferred = read_field("Default account type [checking/savings] (optional): ")
                customer = bank.create_customer(
                    name,
                    legal_name=legal_name,
                    location=location,
                    preferred_account_type=preferred,
                )
                draw_screen(
                    "CUSTOMER CREATED",
                    [f"Customer ID: {customer.customer_id}", f"Name       : {customer.name}", "STATUS     : ACTIVE"],
                    footer="Press ENTER to continue",
                )
                pause()
                input()
            elif choice == "2":
                draw_screen("OPEN ACCOUNT")
                customer_id = read_field("Customer ID (or PF3): ")
                if customer_id.upper() == "PF3":
                    continue
                account_type = read_field("Account type [checking/savings] (blank uses customer default): ")
                account = bank.open_account(customer_id, account_type)
                draw_screen(
                    "ACCOUNT OPENED",
                    [
                        f"Account ID : {account.account_id}",
                        f"Customer ID: {account.customer_id}",
                        f"Type       : {account.account_type.upper()}",
                    ],
                    footer="Press ENTER to continue",
                )
                pause()
                input()
            elif choice == "3":
                draw_screen("DEPOSIT")
                account_id = read_field("Account ID (or PF3): ")
                if account_id.upper() == "PF3":
                    continue
                amount = read_field("Amount: ")
                tx = bank.deposit(account_id, amount)
                transaction_confirmation("DEPOSIT", tx.transaction_id, [f"ACCOUNT: {account_id}", f"AMOUNT : ${tx.amount}"])
            elif choice == "4":
                draw_screen("WITHDRAW")
                account_id = read_field("Account ID (or PF3): ")
                if account_id.upper() == "PF3":
                    continue
                amount = read_field("Amount: ")
                tx = bank.withdraw(account_id, amount)
                transaction_confirmation("WITHDRAWAL", tx.transaction_id, [f"ACCOUNT: {account_id}", f"AMOUNT : ${tx.amount}"])
            elif choice == "5":
                draw_screen("TRANSFER")
                from_account = read_field("From account (or PF3): ")
                if from_account.upper() == "PF3":
                    continue
                to_account = read_field("To account: ")
                amount = read_field("Amount: ")
                debit, credit = bank.transfer(from_account, to_account, amount)
                transaction_confirmation(
                    "TRANSFER",
                    f"{debit.transaction_id} / {credit.transaction_id}",
                    [f"FROM   : {from_account}", f"TO     : {to_account}", f"AMOUNT : ${debit.amount}"],
                )
            elif choice == "6":
                draw_screen("UPDATE CUSTOMER")
                customer_id = read_field("Customer ID (or PF3): ")
                if customer_id.upper() == "PF3":
                    continue
                name = read_field("Updated display name (optional): ") or None
                legal_name = read_field("Updated legal name (optional): ") or None
                location = read_field("Updated location (optional): ") or None
                preferred = read_field("Updated default account type [checking/savings] (optional): ") or None
                customer = bank.update_customer(
                    customer_id,
                    name=name,
                    legal_name=legal_name,
                    location=location,
                    preferred_account_type=preferred,
                )
                draw_screen("CUSTOMER UPDATED", [f"CUSTOMER ID: {customer.customer_id}"], footer="Press ENTER to continue")
                pause()
                input()
            elif choice == "7":
                draw_screen("FREEZE CUSTOMER")
                customer_id = read_field("Customer ID (or PF3): ")
                if customer_id.upper() == "PF3":
                    continue
                customer = bank.freeze_customer(customer_id)
                draw_screen("CUSTOMER FROZEN", [f"CUSTOMER ID: {customer.customer_id}"], footer="Press ENTER to continue")
                pause()
                input()
            elif choice == "8":
                draw_screen("FLAG CUSTOMER")
                customer_id = read_field("Customer ID (or PF3): ")
                if customer_id.upper() == "PF3":
                    continue
                is_flagged = read_field("Flag customer? [y/n]: ").lower() in {"y", "yes", "1", "true"}
                customer = bank.flag_customer(customer_id, is_flagged)
                draw_screen(
                    "CUSTOMER FLAG UPDATED",
                    [f"CUSTOMER ID: {customer.customer_id}", f"FLAGGED    : {customer.is_flagged}"],
                    footer="Press ENTER to continue",
                )
                pause()
                input()
            elif choice == "9":
                draw_screen("DELETE CUSTOMER")
                customer_id = read_field("Customer ID (or PF3): ")
                if customer_id.upper() == "PF3":
                    continue
                customer = bank.delete_customer(customer_id)
                draw_screen("CUSTOMER DELETED", [f"CUSTOMER ID: {customer.customer_id}"], footer="Press ENTER to continue")
                pause()
                input()
            elif choice == "10":
                draw_screen("CUSTOMER STATUS")
                customer_id = read_field("Customer ID (or PF3): ")
                if customer_id.upper() == "PF3":
                    continue
                status = bank.get_customer_status(customer_id)
                draw_screen(
                    "CUSTOMER STATUS RESULT",
                    [
                        f"CUSTOMER ID  : {status['customer_id']}",
                        f"STATUS       : {status['status'].upper()}",
                        f"FLAGGED      : {status['is_flagged']}",
                        f"ACCOUNT COUNT: {status['account_count']}",
                        f"OPEN ACCOUNTS: {status['open_accounts']}",
                        f"TOTAL ASSETS : ${status['total_assets']}",
                    ],
                    footer="Press ENTER to continue",
                )
                input()
            elif choice == "11":
                draw_screen(
                    "END OF DAY REPORT",
                    bank.end_of_day_report().splitlines(),
                    footer="Press ENTER to continue",
                )
                input()
            elif choice == "12":
                lookup_account_screen(bank)
            elif choice == "13":
                draw_screen("SESSION COMPLETE", ["Goodbye."], footer="Press ENTER to close")
                pause()
                input()
                break
            else:
                draw_screen(
                    "MAINFRAME ERROR PANEL",
                    ["ERROR CODE: MBE-001", "MESSAGE   : Unknown menu option"],
                    footer="Press ENTER to continue",
                )
                input()
        except ValueError as exc:
            render_error(exc)


if __name__ == "__main__":
    main()
