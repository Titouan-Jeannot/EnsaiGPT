from datetime import datetime
import time
import pytest

from DAO.DBConnector import DBConnection
from DAO.FeedbackDAO import FeedbackDAO
from ObjetMetier.Feedback import Feedback


def _table_exists(name: str) -> bool:
    try:
        with DBConnection().connection as c:
            with c.cursor() as cur:
                cur.execute("""
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_name=%s
                    LIMIT 1;
                """, (name,))
                return cur.fetchone() is not None
    except Exception:
        return False


def _pick_id(table: str, col: str):
    try:
        with DBConnection().connection as c:
            with c.cursor() as cur:
                cur.execute(f"SELECT {col} FROM {table} ORDER BY {col} DESC LIMIT 1;")
                r = cur.fetchone()
                if not r:
                    return None
                return r[col] if isinstance(r, dict) else r[0]
    except Exception:
        return None


def _read_returning_id(row, key: str) -> int:
    """Compat: row peut être un dict (RealDictCursor) ou un tuple."""
    if row is None:
        raise RuntimeError("RETURNING n'a renvoyé aucune ligne")
    if isinstance(row, dict):
        return row[key]
    return row[0]


def _ensure_user() -> int:
    """
    Crée un user minimal conforme au schéma si aucun n'existe.
    users: username, nom, prenom, mail, password_hash (obligatoires)
    """
    uid = _pick_id("users", "id_user")
    if uid is not None:
        return uid

    suffix = str(int(time.time() * 1000000))
    username = f"it_user_{suffix}"
    mail = f"it_user_{suffix}@example.com"

    with DBConnection().connection as c:
        with c.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (username, nom, prenom, mail, password_hash, salt, status, setting_param)
                VALUES (%s, %s, %s, %s, %s, %s, 'active', %s)
                RETURNING id_user;
                """,
                (
                    username,
                    "Integration",
                    "Test",
                    mail,
                    "pbkdf2:sha256:260000$itest$deadbeef",
                    "randomsalt",
                    None,
                ),
            )
            row = cur.fetchone()
            uid = _read_returning_id(row, "id_user")
        c.commit()
    return uid


def _ensure_conversation() -> int:
    """
    Crée une conversation minimale si aucune n'existe.
    conversation: titre, created_at, settings_conversation, token_viewer, token_writter, is_active
    """
    conv_id = _pick_id("conversation", "id_conversation")
    if conv_id is not None:
        return conv_id

    with DBConnection().connection as c:
        with c.cursor() as cur:
            cur.execute(
                """
                INSERT INTO conversation (titre, created_at, settings_conversation, token_viewer, token_writter, is_active)
                VALUES (%s, NOW(), %s, %s, %s, TRUE)
                RETURNING id_conversation;
                """,
                ("IT conversation", "{}", "tv-it", "tw-it"),
            )
            row = cur.fetchone()
            conv_id = _read_returning_id(row, "id_conversation")
        c.commit()
    return conv_id


def _ensure_message(user_id: int, conv_id: int) -> int:
    """
    Crée un message minimal si aucun n'existe.
    message: id_conversation, id_user, "timestamp", message, is_from_agent
    """
    mid = _pick_id("message", "id_message")
    if mid is not None:
        return mid

    with DBConnection().connection as c:
        with c.cursor() as cur:
            cur.execute(
                """
                INSERT INTO message (id_conversation, id_user, "timestamp", message, is_from_agent)
                VALUES (%s, %s, NOW(), %s, %s)
                RETURNING id_message;
                """,
                (conv_id, user_id, "message IT", False),
            )
            row = cur.fetchone()
            mid = _read_returning_id(row, "id_message")
        c.commit()
    return mid


@pytest.fixture(scope="module")
def infra_ok():
    # 1) Présence des tables minimales
    required = ["users", "conversation", "message", "feedback"]
    missing = [t for t in required if not _table_exists(t)]
    if missing:
        pytest.fail(f"Infra DB incomplète: tables manquantes {missing}")

    # 2) Provision
    uid = _ensure_user()
    conv_id = _ensure_conversation()
    mid = _ensure_message(uid, conv_id)
    return uid, mid


@pytest.mark.integration
def test_crud_and_queries(infra_ok):
    user_id, message_id = infra_ok
    dao = FeedbackDAO()

    # CREATE
    created = dao.create(Feedback(
        id_feedback=0,
        id_user=user_id,
        id_message=message_id,
        is_like=True,
        comment="it-test",
        created_at=datetime.now(),
    ))
    assert created.id_feedback and created.is_like is True

    # READ
    got = dao.read(created.id_feedback)
    assert got is not None and got.id_feedback == created.id_feedback

    # UPDATE
    created.comment = "it-test-upd"
    created.is_like = False
    assert dao.update(created) is True
    got2 = dao.read(created.id_feedback)
    assert got2.comment == "it-test-upd" and got2.is_like is False

    # QUERIES
    lst_by_msg = dao.find_by_message(message_id)
    assert any(f.id_feedback == created.id_feedback for f in lst_by_msg)
    lst_by_user = dao.find_by_user(user_id)
    assert any(f.id_feedback == created.id_feedback for f in lst_by_user)
    likes = dao.count_likes(message_id)
    dislikes = dao.count_dislikes(message_id)
    assert isinstance(likes, int) and isinstance(dislikes, int)

    # DELETE
    assert dao.delete(created.id_feedback) is True
