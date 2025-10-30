SCHEMA_SQL = """
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_status_enum') THEN
    CREATE TYPE user_status_enum AS ENUM ('active', 'deleted', 'banni');
  END IF;
END$$;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'collaboration_role_enum') THEN
    CREATE TYPE collaboration_role_enum AS ENUM ('admin', 'writer', 'viewer', 'banni');
  END IF;
END$$;

CREATE TABLE IF NOT EXISTS users (
  id_user         BIGSERIAL PRIMARY KEY,
  username        VARCHAR(50)  NOT NULL UNIQUE,
  nom             VARCHAR(255) NOT NULL,
  prenom          VARCHAR(255) NOT NULL,
  mail            VARCHAR(255) NOT NULL UNIQUE,
  password_hash   VARCHAR(255) NOT NULL,
  sign_in_date    TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
  last_login      TIMESTAMPTZ,
  status          user_status_enum NOT NULL DEFAULT 'active',
  setting_param   VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS conversation (
  id_conversation       BIGSERIAL PRIMARY KEY,
  titre                 VARCHAR(255) NOT NULL,
  created_at            TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
  settings_conversation TEXT,
  token_viewer          VARCHAR(255),
  token_writter         VARCHAR(255),
  is_active             BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS message (
  id_message      BIGSERIAL PRIMARY KEY,
  id_conversation BIGINT NOT NULL
                   REFERENCES conversation(id_conversation) ON DELETE CASCADE,
  id_user         BIGINT
                   REFERENCES users(id_user) ON DELETE SET NULL,
  "timestamp"     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  message         TEXT        NOT NULL,
  is_from_agent   BOOLEAN     NOT NULL DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_message_conversation ON message(id_conversation);
CREATE INDEX IF NOT EXISTS idx_message_user         ON message(id_user);
CREATE INDEX IF NOT EXISTS idx_message_timestamp    ON message("timestamp");

CREATE TABLE IF NOT EXISTS mots_bannis (
  id_mot BIGSERIAL PRIMARY KEY,
  mot    VARCHAR(255) NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_mots_bannis_mot ON mots_bannis(LOWER(mot));

CREATE TABLE IF NOT EXISTS feedback (
  id_feedback BIGSERIAL PRIMARY KEY,
  id_user     BIGINT
               REFERENCES users(id_user) ON DELETE SET NULL,
  id_message  BIGINT NOT NULL
               REFERENCES message(id_message) ON DELETE CASCADE,
  is_like     BOOLEAN NOT NULL,
  comment     VARCHAR(1000),
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_feedback_message ON feedback(id_message);
CREATE INDEX IF NOT EXISTS idx_feedback_user    ON feedback(id_user);

CREATE TABLE IF NOT EXISTS collaboration (
  id_collaboration BIGSERIAL PRIMARY KEY,
  id_conversation  BIGINT NOT NULL
                    REFERENCES conversation(id_conversation) ON DELETE CASCADE,
  id_user          BIGINT NOT NULL
                    REFERENCES users(id_user) ON DELETE CASCADE,
  role             collaboration_role_enum NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_collaboration_unique
  ON collaboration(id_conversation, id_user);
CREATE INDEX IF NOT EXISTS idx_collaboration_role ON collaboration(role);
"""
