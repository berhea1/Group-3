BEGIN;

CREATE TYPE user_role AS ENUM ('admin', 'student', 'worker');
CREATE TYPE machine_status AS ENUM ('active', 'maintenance', 'locked_out');
CREATE TYPE access_result AS ENUM ('approved', 'denied');

CREATE TABLE users (
  id BIGSERIAL PRIMARY KEY,
  role user_role NOT NULL DEFAULT 'student',
  full_name TEXT NOT NULL,
  barcode_value TEXT NOT NULL UNIQUE,
  email TEXT,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE machines (
  id BIGSERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  kiosk_id TEXT NOT NULL UNIQUE,
  location TEXT,
  status machine_status NOT NULL DEFAULT 'active',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE certifications (
  id BIGSERIAL PRIMARY KEY,
  code TEXT NOT NULL UNIQUE,
  title TEXT NOT NULL,
  description TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE user_certifications (
  user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  certification_id BIGINT NOT NULL REFERENCES certifications(id) ON DELETE CASCADE,
  granted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  expires_at TIMESTAMPTZ,
  granted_by BIGINT REFERENCES users(id),
  PRIMARY KEY (user_id, certification_id)
);

CREATE TABLE machine_requirements (
  machine_id BIGINT NOT NULL REFERENCES machines(id) ON DELETE CASCADE,
  certification_id BIGINT NOT NULL REFERENCES certifications(id) ON DELETE CASCADE,
  PRIMARY KEY (machine_id, certification_id)
);

CREATE TABLE access_sessions (
  id BIGSERIAL PRIMARY KEY,
  machine_id BIGINT NOT NULL REFERENCES machines(id) ON DELETE RESTRICT,
  user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
  barcode_value TEXT NOT NULL,
  result access_result NOT NULL,
  deny_reason TEXT,
  started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  ended_at TIMESTAMPTZ,
  approved_until TIMESTAMPTZ,
  override_by BIGINT REFERENCES users(id) ON DELETE SET NULL,
  kiosk_device_id TEXT
);

CREATE TABLE admin_accounts (
  id BIGSERIAL PRIMARY KEY,
  username TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  user_id BIGINT UNIQUE REFERENCES users(id) ON DELETE SET NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_barcode ON users(barcode_value);
CREATE INDEX idx_machines_kiosk_id ON machines(kiosk_id);
CREATE INDEX idx_sessions_machine_time ON access_sessions(machine_id, started_at DESC);
CREATE INDEX idx_sessions_user_time ON access_sessions(user_id, started_at DESC);

INSERT INTO machines (name, kiosk_id, location)
VALUES ('Laser Cutter #1', 'laser-01', 'Room A');
INSERT INTO certifications (code, title)
VALUES ('LASER_BASIC', 'Laser Cutter Basic');
INSERT INTO machine_requirements (machine_id, certification_id)
SELECT m.id, c.id FROM machines m CROSS JOIN certifications c
WHERE m.kiosk_id = 'laser-01' AND c.code = 'LASER_BASIC';
INSERT INTO users (role, full_name, barcode_value)
VALUES ('student', 'Test Student', '1234567890');
INSERT INTO user_certifications (user_id, certification_id)
SELECT u.id, c.id FROM users u CROSS JOIN certifications c
WHERE u.barcode_value = '1234567890' AND c.code = 'LASER_BASIC';

COMMIT;
