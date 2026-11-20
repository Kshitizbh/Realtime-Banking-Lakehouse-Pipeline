-- Core-banking OLTP source: customers + accounts.
-- Runs ONCE, on the first start of an empty postgres_data volume.
-- To re-run it: make reset-postgres  (drops the volume - local data only).
--
-- updated_at is maintained by a trigger on every UPDATE, so your M1 extract
-- can pull only changed rows (WHERE updated_at > last_watermark).

CREATE SCHEMA IF NOT EXISTS core_banking;
SET search_path TO core_banking;

-- ---------- tables ----------
CREATE TABLE customers (
    customer_id    VARCHAR(20) PRIMARY KEY,
    customer_name  TEXT        NOT NULL,
    segment        TEXT        NOT NULL,
    age_band       TEXT        NOT NULL,
    province       TEXT        NOT NULL,
    risk_band      TEXT        NOT NULL,
    created_date   DATE        NOT NULL,
    is_active      BOOLEAN     NOT NULL,
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE accounts (
    account_id     VARCHAR(20) PRIMARY KEY,
    customer_id    VARCHAR(20) NOT NULL REFERENCES customers (customer_id),
    branch_id      VARCHAR(10) NOT NULL,
    account_type   TEXT        NOT NULL,
    account_status TEXT        NOT NULL,
    opened_date    DATE        NOT NULL,
    currency       CHAR(3)     NOT NULL,
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_customers_updated_at ON customers (updated_at);
CREATE INDEX idx_accounts_updated_at  ON accounts (updated_at);

-- ---------- keep updated_at honest ----------
CREATE OR REPLACE FUNCTION set_updated_at() RETURNS trigger AS $$
BEGIN
    NEW.updated_at := now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_customers_updated_at BEFORE UPDATE ON customers
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_accounts_updated_at BEFORE UPDATE ON accounts
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ---------- seed from the snapshot files (mounted read-only at /seed) ----------
-- Load everything as text first, then cast explicitly: the account snapshot
-- uses M/D/YYYY dates while the customer snapshot uses ISO dates.
CREATE TEMP TABLE stg_customers (
    customer_id TEXT, customer_name TEXT, segment TEXT, age_band TEXT, province TEXT,
    risk_band TEXT, created_date TEXT, snapshot_date TEXT, is_active TEXT
);
COPY stg_customers FROM '/seed/customers/customer_snapshot_2026-01-01.csv'
    WITH (FORMAT csv, HEADER true);

INSERT INTO customers (customer_id, customer_name, segment, age_band, province,
                       risk_band, created_date, is_active, updated_at)
SELECT customer_id, customer_name, segment, age_band, province, risk_band,
       created_date::date, is_active::boolean,
       snapshot_date::date::timestamptz
FROM stg_customers;

CREATE TEMP TABLE stg_accounts (
    account_id TEXT, customer_id TEXT, branch_id TEXT, account_type TEXT,
    account_status TEXT, opened_date TEXT, currency TEXT, snapshot_date TEXT
);
COPY stg_accounts FROM '/seed/accounts/account_snapshot_2026-01-01.csv'
    WITH (FORMAT csv, HEADER true);

INSERT INTO accounts (account_id, customer_id, branch_id, account_type,
                      account_status, opened_date, currency, updated_at)
SELECT account_id, customer_id, branch_id, account_type, account_status,
       to_date(opened_date, 'MM/DD/YYYY'), currency,
       to_date(snapshot_date, 'MM/DD/YYYY')::timestamptz
FROM stg_accounts;

-- Fail the init loudly if the seed is incomplete.
DO $$
BEGIN
    IF (SELECT count(*) FROM customers) <> 5000 THEN
        RAISE EXCEPTION 'Expected 5000 customers, got %', (SELECT count(*) FROM customers);
    END IF;
    IF (SELECT count(*) FROM accounts) <> 8000 THEN
        RAISE EXCEPTION 'Expected 8000 accounts, got %', (SELECT count(*) FROM accounts);
    END IF;
END $$;
