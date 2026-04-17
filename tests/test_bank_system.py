import tempfile
import unittest

from bank_system.core import BankSystem


class BankSystemTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = f"{self.temp_dir.name}/bank.json"
        self.bank = BankSystem(db_path=self.db_path)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_customer_account_and_deposit(self) -> None:
        customer = self.bank.create_customer("Ada Lovelace")
        account = self.bank.open_account(customer.customer_id, "checking")
        self.bank.deposit(account.account_id, "50.25")
        updated = self.bank.get_account(account.account_id)
        self.assertEqual(updated.balance, "50.25")

    def test_withdraw_and_insufficient_funds(self) -> None:
        customer = self.bank.create_customer("Grace Hopper")
        account = self.bank.open_account(customer.customer_id, "savings")
        self.bank.deposit(account.account_id, "40")
        self.bank.withdraw(account.account_id, "10")
        updated = self.bank.get_account(account.account_id)
        self.assertEqual(updated.balance, "30.00")
        with self.assertRaises(ValueError):
            self.bank.withdraw(account.account_id, "999")

    def test_transfer_moves_funds_between_accounts(self) -> None:
        customer = self.bank.create_customer("Katherine Johnson")
        a1 = self.bank.open_account(customer.customer_id, "checking")
        a2 = self.bank.open_account(customer.customer_id, "savings")
        self.bank.deposit(a1.account_id, "125")
        self.bank.transfer(a1.account_id, a2.account_id, "25")

        self.assertEqual(self.bank.get_account(a1.account_id).balance, "100.00")
        self.assertEqual(self.bank.get_account(a2.account_id).balance, "25.00")


if __name__ == "__main__":
    unittest.main()
