from datetime import datetime
import pytest

from src.DAO.DBConnector import DBConnection
from src.DAO.FeedbackDAO import FeedbackDAO
from src.ObjetMetier.Feedback import Feedback


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


@pytest.fixture(scope="module")
def infra_ok():
    if not _table_exists("feedback"):
        pytest.skip("Table 'feedback' absente")
    uid = _pick_id("users", "id_user")
    mid = _pick_id("message", "id_message")
    if uid is None or mid is None:
        pytest.skip("Besoin d'au moins 1 user et 1 message existants")
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
