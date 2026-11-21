-- Core-banking OLTP source: reference tables, customers, accounts.
-- Runs ONCE, on the first start of an empty postgres_data volume.
-- To re-run it: make reset-postgres  (drops the volume - local data only).
--
-- The whole ./data folder is mounted read-only at /seed.
-- updated_at is maintained by a trigger on every UPDATE, so your M1 extract
-- can pull only changed rows (WHERE updated_at > last_watermark).

CREATE SCHEMA IF NOT EXISTS core_banking;
SET search_path TO core_banking;

-- ---------- keep updated_at honest ----------
CREATE OR REPLACE FUNCTION set_updated_at() RETURNS trigger AS $$
BEGIN
    NEW.updated_at := now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ======================================================================
-- Reference tables (small; extracted in full)
-- ======================================================================
CREATE TABLE branches (
    branch_id    VARCHAR(10) PRIMARY KEY,
    branch_name  TEXT        NOT NULL,
    province     TEXT        NOT NULL,
    region       TEXT        NOT NULL,
    opened_date  DATE        NOT NULL,
    is_active    BOOLEAN     NOT NULL,
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE transaction_types (
    transaction_type_code VARCHAR(10) PRIMARY KEY,
    transaction_type_name TEXT        NOT NULL,
    balance_direction     TEXT        NOT NULL CHECK (balance_direction IN ('credit', 'debit', 'mixed')),
    updated_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE merchant_categories (
    merchant_category_code VARCHAR(4)  PRIMARY KEY,
    merchant_category_name TEXT        NOT NULL,
    risk_category          TEXT        NOT NULL CHECK (risk_category IN ('LOW', 'MEDIUM', 'HIGH')),
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Reference files have clean ISO dates and booleans, so they load directly.
COPY branches (branch_id, branch_name, province, region, opened_date, is_active)
    FROM '/seed/reference/branches.csv' WITH (FORMAT csv, HEADER true);
COPY transaction_types (transaction_type_code, transaction_type_name, balance_direction)
    FROM '/seed/reference/transaction_types.csv' WITH (FORMAT csv, HEADER true);
COPY merchant_categories (merchant_category_code, merchant_category_name, risk_category)
    FROM '/seed/reference/merchant_categories.csv' WITH (FORMAT csv, HEADER true);

-- ======================================================================
-- Master data (changes over time; extracted incrementally)
-- ======================================================================
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
    branch_id      VARCHAR(10) NOT NULL REFERENCES branches (branch_id),
    account_type   TEXT        NOT NULL,
    account_status TEXT        NOT NULL,
    opened_date    DATE        NOT NULL,
    currency       CHAR(3)     NOT NULL,
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_customers_updated_at ON customers (updated_at);
CREATE INDEX idx_accounts_updated_at  ON accounts (updated_at);

-- Load everything as text first, then cast explicitly: the account snapshot
-- uses M/D/YYYY dates while the customer snapshot uses ISO dates.
CREATE TEMP TABLE stg_customers (
    customer_id TEXT, customer_name TEXT, segment TEXT, age_band TEXT, province TEXT,
    risk_band TEXT, created_date TEXT, snapshot_date TEXT, is_active TEXT
);
COPY stg_customers FROM '/seed/batch/customers/customer_snapshot_2026-01-01.csv'
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
COPY stg_accounts FROM '/seed/batch/accounts/account_snapshot_2026-01-01.csv'
    WITH (FORMAT csv, HEADER true);

INSERT INTO accounts (account_id, customer_id, branch_id, account_type,
                      account_status, opened_date, currency, updated_at)
SELECT account_id, customer_id, branch_id, account_type, account_status,
       to_date(opened_date, 'MM/DD/YYYY'), currency,
       to_date(snapshot_date, 'MM/DD/YYYY')::timestamptz
FROM stg_accounts;

-- ---------- triggers (created after the seed so seeded rows keep the snapshot time) ----------
CREATE TRIGGER trg_branches_updated_at BEFORE UPDATE ON branches
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_transaction_types_updated_at BEFORE UPDATE ON transaction_types
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_merchant_categories_updated_at BEFORE UPDATE ON merchant_categories
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_customers_updated_at BEFORE UPDATE ON customers
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_accounts_updated_at BEFORE UPDATE ON accounts
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ---------- fail the init loudly if the seed is incomplete ----------
DO $$
DECLARE
    expected CONSTANT jsonb := '{"branches": 40, "transaction_types": 6, "merchant_categories": 8,
                                 "customers": 5000, "accounts": 8000}';
    t   text;
    n   bigint;
BEGIN
    FOR t IN SELECT jsonb_object_keys(expected) LOOP
        EXECUTE format('SELECT count(*) FROM core_banking.%I', t) INTO n;
        IF n <> (expected ->> t)::bigint THEN
            RAISE EXCEPTION 'Seed check failed for %: expected %, got %', t, expected ->> t, n;
        END IF;
    END LOOP;
END $$;
