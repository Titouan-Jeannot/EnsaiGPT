from datetime import datetime, timedelta
import time
import pytest

from DAO.DBConnector import DBConnection
from DAO.MessageDAO import MessageDAO
from ObjetMetier.Message import Message


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
    if row is None:
        raise RuntimeError("RETURNING n'a renvoyé aucune ligne")
    return row[key] if isinstance(row, dict) else row[0]


def _ensure_user() -> int:
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
                    username, "Integration", "Test", mail,
                    "pbkdf2:sha256:260000$itest$deadbeef", "randomsalt", None
                ),
            )
            row = cur.fetchone()
            uid = _read_returning_id(row, "id_user")
        c.commit()
    return uid


def _ensure_conversation() -> int:
    cid = _pick_id("conversation", "id_conversation")
    if cid is not None:
        return cid

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
            cid = _read_returning_id(row, "id_conversation")
        c.commit()
    return cid


def _ensure_message(user_id: int, conv_id: int) -> int:
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
                (conv_id, user_id, "seed msg", False),
            )
            row = cur.fetchone()
            mid = _read_returning_id(row, "id_message")
        c.commit()
    return mid


@pytest.fixture(scope="module")
def infra_ok():
    required = ["users", "conversation", "message"]
    missing = [t for t in required if not _table_exists(t)]
    if missing:
        pytest.fail(f"Infra DB incomplète: {missing}")
    uid = _ensure_user()
    cid = _ensure_conversation()
    mid = _ensure_message(uid, cid)
    return uid, cid, mid


@pytest.mark.integration
def test_crud_and_queries(infra_ok):
    user_id, conv_id, _ = infra_ok
    dao = MessageDAO()

    # CREATE
    m = Message(
        id_message=None,
        id_conversation=conv_id,
        id_user=user_id,
        datetime=datetime.now(),
        message="integration create",
        is_from_agent=False,
    )
    created = dao.create(m)
    assert created.id_message is not None

    # READ
    got = dao.get_by_id(created.id_message)
    assert got is not None and got.message == "integration create"

    # UPDATE
    got.message = "integration updated"
    assert dao.update(got) is True
    got2 = dao.get_by_id(created.id_message)
    assert got2.message == "integration updated"

    # COUNT
    n = dao.count_messages_by_conversation(conv_id)
    assert isinstance(n, int) and n >= 1

    # LIST BY CONVERSATION
    lst = dao.get_messages_by_conversation(conv_id)
    assert any(x.id_message == created.id_message for x in lst)

    # PAGINATION
    paged = dao.get_messages_by_conversation_paginated(conv_id, page=1, per_page=2)
    assert len(paged) >= 1

    # SEARCH (single conv wrapper)
    direct_search = dao.search_messages(conv_id, "updated")
    assert any(x.id_message == created.id_message for x in direct_search)

    # SEARCH multi-conv
    multi = dao.search_by_keyword("updated", [conv_id])
    assert any(x.id_message == created.id_message for x in multi)

    # SEARCH BY DATE (multi-conv)
    day = datetime.now()
    by_date = dao.search_by_date(day, [conv_id])
    assert isinstance(by_date, list)

    # RANGE
    start = datetime.now() - timedelta(days=1)
    end = datetime.now() + timedelta(days=1)
    in_range = dao.get_messages_by_date_range(conv_id, start, end)
    assert any(x.id_message == created.id_message for x in in_range)

    # LAST MESSAGE
    last = dao.get_last_message(conv_id)
    assert last is not None

    # DELETE
    assert dao.delete_by_id(created.id_message) is True
    assert dao.get_by_id(created.id_message) is None
