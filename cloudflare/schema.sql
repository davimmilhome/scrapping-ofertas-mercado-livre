CREATE TABLE IF NOT EXISTS offer_snapshots (
  id BIGSERIAL PRIMARY KEY,
  marketplace VARCHAR(64) NOT NULL,
  listing_id VARCHAR(64) NOT NULL,
  observed_on DATE NOT NULL,
  title VARCHAR(1024) NOT NULL,
  url VARCHAR(4096) NOT NULL,
  price NUMERIC(18, 2) NOT NULL,
  previous_price NUMERIC(18, 2),
  seller VARCHAR(1024),
  page INTEGER NOT NULL,
  collected_at TIMESTAMPTZ NOT NULL,
  CONSTRAINT uq_offer_daily UNIQUE (marketplace, listing_id, observed_on)
);

CREATE TABLE IF NOT EXISTS collection_runs (
  run_id VARCHAR(32) PRIMARY KEY,
  status VARCHAR(16) NOT NULL,
  app_env VARCHAR(16) NOT NULL,
  runner VARCHAR(32) NOT NULL,
  started_at TIMESTAMPTZ NOT NULL,
  finished_at TIMESTAMPTZ,
  duration_seconds NUMERIC(12, 3),
  max_duration_seconds NUMERIC(12, 3) NOT NULL,
  pages_requested INTEGER NOT NULL,
  pages_ok INTEGER NOT NULL DEFAULT 0,
  offers_found INTEGER NOT NULL DEFAULT 0,
  failures_count INTEGER NOT NULL DEFAULT 0,
  rejected_count INTEGER NOT NULL DEFAULT 0,
  error_summary VARCHAR(1000)
);
