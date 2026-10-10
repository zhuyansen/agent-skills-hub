"""Build the code-review test fixture: a small order service with 12 pull-request branches.

  python ops/review-runs/make_fixture.py      # writes in/input/shop (a git repo) and truth.json

Eight branches each carry one planted, checkable defect; four are clean changes. A reviewer
is run on every branch against main; truth.json says what each branch hides (it stays
outside in/, so the sandbox never sees it). The design follows SWR-Bench (arXiv 2509.01494):
pull requests with known issues and clean ones, so a tool gets two numbers, defects found
and false alarms.
"""
import json
import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).parent
REPO = HERE / "in" / "input" / "shop"

BASE = {
    "README.md": "# shop\n\nA small order service: orders, stock, payments. Pure Python, no dependencies.\nRun the tests with `python -m unittest`.\n",
    "shop/__init__.py": "",
    "shop/db.py": '''"""A tiny in-memory store with a SQL-like query helper (backed by sqlite3)."""
import sqlite3

_conn = sqlite3.connect(":memory:", check_same_thread=False)
_conn.execute("create table orders (id integer primary key, user_id integer, status text, total_cents integer, note text)")
_conn.execute("create table stock (sku text primary key, available integer)")


def query(sql: str, params: tuple = ()) -> list[tuple]:
    return _conn.execute(sql, params).fetchall()


def execute(sql: str, params: tuple = ()) -> int:
    cur = _conn.execute(sql, params)
    _conn.commit()
    return cur.lastrowid
''',
    "shop/orders.py": '''"""Orders: create, list, look up."""
from shop import db

PAGE_SIZE = 20


class NotFound(Exception):
    pass


class Forbidden(Exception):
    pass


def create_order(user_id: int, total_cents: int, note: str = "") -> int:
    return db.execute("insert into orders (user_id, status, total_cents, note) values (?, 'new', ?, ?)",
                      (user_id, total_cents, note))


def get_order(order_id: int, user_id: int) -> tuple:
    rows = db.query("select id, user_id, status, total_cents, note from orders where id = ?", (order_id,))
    if not rows:
        raise NotFound(order_id)
    if rows[0][1] != user_id:
        raise Forbidden(order_id)
    return rows[0]


def list_orders(user_id: int) -> list[tuple]:
    return db.query("select id, status, total_cents from orders where user_id = ? order by id", (user_id,))
''',
    "shop/stock.py": '''"""Stock: reserve units of a SKU."""
from shop import db


class OutOfStock(Exception):
    pass


def set_stock(sku: str, available: int) -> None:
    db.execute("insert or replace into stock (sku, available) values (?, ?)", (sku, available))


def available(sku: str) -> int:
    rows = db.query("select available from stock where sku = ?", (sku,))
    return rows[0][0] if rows else 0


def reserve(sku: str, qty: int) -> None:
    if available(sku) < qty:
        raise OutOfStock(sku)
    db.execute("update stock set available = available - ? where sku = ?", (qty, sku))
''',
    "shop/payments.py": '''"""Payments: capture an order's total through a gateway."""
import logging

from shop import db

log = logging.getLogger("shop.payments")


class PaymentError(Exception):
    pass


class Gateway:
    """Stand-in for a card gateway; `fail` makes the next captures raise."""
    def __init__(self) -> None:
        self.fail = 0
        self.captured: list[tuple[int, int]] = []

    def capture(self, order_id: int, amount_cents: int, card_token: str) -> None:
        if self.fail > 0:
            self.fail -= 1
            raise PaymentError("gateway timeout")
        self.captured.append((order_id, amount_cents))


def pay(gateway: Gateway, order_id: int, amount_cents: int, card_token: str) -> None:
    gateway.capture(order_id, amount_cents, card_token)
    db.execute("update orders set status = 'paid' where id = ?", (order_id,))
    log.info("order %s paid", order_id)
''',
    "tests/__init__.py": "",
    "tests/test_shop.py": '''import unittest

from shop import orders, payments, stock


class ShopTest(unittest.TestCase):
    def test_owner_reads_own_order(self):
        oid = orders.create_order(1, 500)
        self.assertEqual(orders.get_order(oid, 1)[3], 500)

    def test_other_user_is_forbidden(self):
        oid = orders.create_order(1, 500)
        with self.assertRaises(orders.Forbidden):
            orders.get_order(oid, 2)

    def test_reserve_reduces_stock(self):
        stock.set_stock("A", 5)
        stock.reserve("A", 2)
        self.assertEqual(stock.available("A"), 3)

    def test_reserve_more_than_available_fails(self):
        stock.set_stock("B", 1)
        with self.assertRaises(stock.OutOfStock):
            stock.reserve("B", 2)

    def test_pay_marks_order_paid(self):
        oid = orders.create_order(1, 700)
        payments.pay(payments.Gateway(), oid, 700, "tok_test")
        self.assertEqual(orders.get_order(oid, 1)[2], "paid")


if __name__ == "__main__":
    unittest.main()
''',
}

# branch -> (title, {path: (old, new)}, defect or None). Order is mixed so position tells nothing.
PRS = {
    "pr-01-list-pagination": ("Add pagination to list_orders", {
        "shop/orders.py": ('''def list_orders(user_id: int) -> list[tuple]:
    return db.query("select id, status, total_cents from orders where user_id = ? order by id", (user_id,))
''', '''def list_orders(user_id: int, page: int = 1) -> list[tuple]:
    """One page of the user's orders; pages start at 1."""
    offset = page * PAGE_SIZE
    return db.query("select id, status, total_cents from orders where user_id = ? order by id limit ? offset ?",
                    (user_id, PAGE_SIZE, offset))
''')},
        "Off-by-one in pagination: pages start at 1 but offset = page * PAGE_SIZE, so page 1 skips the first 20 orders (should be (page - 1) * PAGE_SIZE)."),
    "pr-02-extract-row-helper": ("Extract the order row lookup into a helper", {
        "shop/orders.py": ('''def get_order(order_id: int, user_id: int) -> tuple:
    rows = db.query("select id, user_id, status, total_cents, note from orders where id = ?", (order_id,))
    if not rows:
        raise NotFound(order_id)
    if rows[0][1] != user_id:
        raise Forbidden(order_id)
    return rows[0]
''', '''def _row(order_id: int) -> tuple:
    rows = db.query("select id, user_id, status, total_cents, note from orders where id = ?", (order_id,))
    if not rows:
        raise NotFound(order_id)
    return rows[0]


def get_order(order_id: int, user_id: int) -> tuple:
    row = _row(order_id)
    if row[1] != user_id:
        raise Forbidden(order_id)
    return row
''')}, None),
    "pr-03-search-by-note": ("Search a user's orders by note text", {
        "shop/orders.py": ('''def list_orders(user_id: int) -> list[tuple]:''', '''def search_orders(user_id: int, text: str) -> list[tuple]:
    """Orders of this user whose note contains `text`."""
    sql = f"select id, status, total_cents from orders where user_id = {user_id} and note like '%{text}%' order by id"
    return db.query(sql)


def list_orders(user_id: int) -> list[tuple]:''')},
        "SQL injection: search_orders builds the query with an f-string from user-supplied text instead of parameters."),
    "pr-04-payment-logging": ("Log payment attempts for support", {
        "shop/payments.py": ('''    gateway.capture(order_id, amount_cents, card_token)
    db.execute("update orders set status = 'paid' where id = ?", (order_id,))
    log.info("order %s paid", order_id)
''', '''    log.info("capturing order %s amount %s with card token %s", order_id, amount_cents, card_token)
    gateway.capture(order_id, amount_cents, card_token)
    db.execute("update orders set status = 'paid' where id = ?", (order_id,))
    log.info("order %s paid", order_id)
''')},
        "Secret in logs: the card token is written to the application log."),
    "pr-05-docstrings-and-types": ("Add docstrings and type hints to stock", {
        "shop/stock.py": ('''def set_stock(sku: str, available: int) -> None:
    db.execute(''', '''def set_stock(sku: str, available: int) -> None:
    """Set how many units of `sku` can be reserved, replacing any earlier value."""
    db.execute('''),
    }, None),
    "pr-06-cancel-order": ("Let users cancel an order", {
        "shop/orders.py": ('''def list_orders(user_id: int) -> list[tuple]:''', '''def cancel_order(order_id: int, user_id: int) -> None:
    """Cancel an order that has not been paid."""
    rows = db.query("select status from orders where id = ?", (order_id,))
    if not rows:
        raise NotFound(order_id)
    if rows[0][0] == "paid":
        raise ValueError("paid orders cannot be cancelled")
    db.execute("update orders set status = 'cancelled' where id = ?", (order_id,))


def list_orders(user_id: int) -> list[tuple]:''')},
        "Missing authorization: cancel_order takes user_id but never checks that the order belongs to that user, so any user can cancel anyone's order."),
    "pr-07-payment-retry": ("Retry a failed capture up to three times", {
        "shop/payments.py": ('''def pay(gateway: Gateway, order_id: int, amount_cents: int, card_token: str) -> None:
    gateway.capture(order_id, amount_cents, card_token)
''', '''MAX_ATTEMPTS = 3


def pay(gateway: Gateway, order_id: int, amount_cents: int, card_token: str) -> None:
    attempt = 1
    while attempt <= MAX_ATTEMPTS:
        try:
            gateway.capture(order_id, amount_cents, card_token)
            break
        except PaymentError:
            log.warning("capture failed for order %s, attempt %s", order_id, attempt)
''')},
        "Retry loop never ends and hides failure: `attempt` is never incremented, so a gateway that keeps failing loops forever (and after three real failures the order would still be marked paid, since nothing re-raises)."),
    "pr-08-validate-create-order": ("Validate input when creating an order", {
        "shop/orders.py": ('''def create_order(user_id: int, total_cents: int, note: str = "") -> int:
    return db.execute(''', '''MAX_NOTE = 500


def create_order(user_id: int, total_cents: int, note: str = "") -> int:
    if total_cents <= 0:
        raise ValueError("total_cents must be positive")
    if len(note) > MAX_NOTE:
        raise ValueError(f"note is longer than {MAX_NOTE} characters")
    return db.execute('''),
        "tests/test_shop.py": ('''    def test_reserve_reduces_stock(self):''', '''    def test_create_order_rejects_non_positive_total(self):
        with self.assertRaises(ValueError):
            orders.create_order(1, 0)

    def test_reserve_reduces_stock(self):''')}, None),
    "pr-09-capture-errors": ("Do not crash checkout when the gateway errors", {
        "shop/payments.py": ('''    gateway.capture(order_id, amount_cents, card_token)
    db.execute("update orders set status = 'paid' where id = ?", (order_id,))
''', '''    try:
        gateway.capture(order_id, amount_cents, card_token)
    except Exception:
        pass
    db.execute("update orders set status = 'paid' where id = ?", (order_id,))
''')},
        "Swallowed exception: a failed capture is ignored and the order is still marked paid."),
    "pr-10-reserve-check": ("Tidy the stock reservation check", {
        "shop/stock.py": ('''    if available(sku) < qty:
        raise OutOfStock(sku)
''', '''    in_stock = available(sku)
    if in_stock > qty:
        raise OutOfStock(sku)
''')},
        "Inverted condition: reserve now raises OutOfStock when there is MORE stock than requested and allows reserving more than is available."),
    "pr-11-test-list-orders": ("Add a test for list_orders", {
        "tests/test_shop.py": ('''    def test_reserve_reduces_stock(self):''', '''    def test_list_orders_returns_only_own_orders(self):
        mine = orders.create_order(41, 100)
        orders.create_order(42, 200)
        self.assertEqual([row[0] for row in orders.list_orders(41)], [mine])

    def test_reserve_reduces_stock(self):''')}, None),
    "pr-12-speed-up-tests": ("Make the forbidden-order test less flaky", {
        "tests/test_shop.py": ('''        oid = orders.create_order(1, 500)
        with self.assertRaises(orders.Forbidden):
            orders.get_order(oid, 2)
''', '''        oid = orders.create_order(1, 500)
        try:
            orders.get_order(oid, 2)
        except orders.Forbidden:
            pass
''')},
        "Test weakened: the assertion that another user is forbidden was replaced by a try/except that passes whether or not Forbidden is raised."),
}


def git(*args: str) -> None:
    subprocess.run(["git", "-C", str(REPO), "-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid", *args],
                   check=True, capture_output=True)


def write(files: dict) -> None:
    for path, text in files.items():
        f = REPO / path
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(text)


def main() -> None:
    shutil.rmtree(REPO, ignore_errors=True)
    REPO.mkdir(parents=True)
    subprocess.run(["git", "init", "-q", "-b", "main", str(REPO)], check=True)
    write(BASE); git("add", "-A"); git("commit", "-q", "-m", "Order service: orders, stock, payments")
    truth = {}
    for branch, (title, edits, defect) in PRS.items():
        git("checkout", "-q", "-b", branch, "main")
        for path, (old, new) in edits.items():
            text = (REPO / path).read_text()
            assert text.count(old) == 1, (branch, path)
            (REPO / path).write_text(text.replace(old, new))
        git("add", "-A"); git("commit", "-q", "-m", title)
        truth[branch] = {"title": title, "defect": defect}
    git("checkout", "-q", "main")
    (HERE / "truth.json").write_text(json.dumps(truth, indent=1))
    print(f"{len(PRS)} branches, {sum(v['defect'] is not None for v in truth.values())} with a planted defect -> {REPO}")


if __name__ == "__main__":
    main()
