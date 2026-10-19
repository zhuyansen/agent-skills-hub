"""Each transaction sets its own statement timeout, so a value another client left on a
pooled connection (Supabase's transaction pooler keeps session SETs) never applies to us."""
from app import database


def test_every_transaction_sets_its_own_statement_timeout():
    sent = []

    class _Conn:
        def exec_driver_sql(self, sql):
            sent.append(sql)

    database._own_statement_timeout(_Conn())
    assert sent == ["SET LOCAL statement_timeout = '120s'"]
