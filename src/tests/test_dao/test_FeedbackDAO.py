from datetime import datetime
from unittest.mock import patch, MagicMock
import pytest

from DAO.FeedbackDAO import FeedbackDAO
from ObjetMetier.Feedback import Feedback


def make_mock_db(rows=None, one=None, rowcount=1):
    cur = MagicMock()
    cur.fetchall.return_value = rows or []
    cur.fetchone.return_value = one
    cur.rowcount = rowcount

    conn = MagicMock()
    conn.cursor.return_value.__enter__.return_value = cur
    conn.__enter__.return_value = conn

    db = MagicMock()
    db.connection = conn
    return db, conn, cur


def make_feedback(**kw):
    now = kw.pop("created_at", datetime(2025, 1, 1, 12))
    return Feedback(
        id_feedback=kw.get("id_feedback", 0),
        id_user=kw.get("id_user", 10),
        id_message=kw.get("id_message", 20),
        is_like=kw.get("is_like", True),
        comment=kw.get("comment", "ok"),
        created_at=now,
    )


def test_create_success():
    with patch("DAO.FeedbackDAO.DBConnection") as MockDBC:
        db, conn, cur = make_mock_db(one={
            "id_feedback": 111, "id_user": 10, "id_message": 20,
            "is_like": True, "comment": "ok", "created_at": datetime(2025,1,1,12),
        })
        MockDBC.return_value = db

        dao = FeedbackDAO()
        out = dao.create(make_feedback(id_feedback=0))

        assert isinstance(out, Feedback)
        assert out.id_feedback == 111
        cur.execute.assert_called_once()


def test_read_found():
    with patch("DAO.FeedbackDAO.DBConnection") as MockDBC:
        db, conn, cur = make_mock_db(one={
            "id_feedback": 5, "id_user": 1, "id_message": 2,
            "is_like": False, "comment": "meh", "created_at": datetime(2025,1,1,10),
        })
        MockDBC.return_value = db

        dao = FeedbackDAO()
        fb = dao.read(5)
        assert fb is not None and fb.id_feedback == 5 and fb.is_like is False


def test_read_not_found():
    with patch("DAO.FeedbackDAO.DBConnection") as MockDBC:
        db, conn, cur = make_mock_db(one=None)
        MockDBC.return_value = db
        dao = FeedbackDAO()
        fb = dao.read(404)
        assert fb is None


def test_update_success():
    with patch("DAO.FeedbackDAO.DBConnection") as MockDBC:
        db, conn, cur = make_mock_db(rowcount=1)
        MockDBC.return_value = db
        dao = FeedbackDAO()
        ok = dao.update(make_feedback(id_feedback=77, is_like=False, comment="x"))
        assert ok is True
        cur.execute.assert_called_once()


def test_delete_success():
    with patch("DAO.FeedbackDAO.DBConnection") as MockDBC:
        db, conn, cur = make_mock_db(rowcount=1)
        MockDBC.return_value = db
        dao = FeedbackDAO()
        assert dao.delete(9) is True


def test_find_by_message():
    with patch("DAO.FeedbackDAO.DBConnection") as MockDBC:
        db, conn, cur = make_mock_db(rows=[
            {"id_feedback": 1, "id_user": 10, "id_message": 99, "is_like": True, "comment": "A", "created_at": datetime(2025,1,1,10)},
            {"id_feedback": 2, "id_user": 11, "id_message": 99, "is_like": False, "comment": "B", "created_at": datetime(2025,1,1,11)},
        ])
        MockDBC.return_value = db
        dao = FeedbackDAO()
        lst = dao.find_by_message(99)
        assert len(lst) == 2 and lst[0].id_feedback == 1 and lst[1].is_like is False


def test_find_by_user():
    with patch("DAO.FeedbackDAO.DBConnection") as MockDBC:
        db, conn, cur = make_mock_db(rows=[
            {"id_feedback": 3, "id_user": 7, "id_message": 50, "is_like": True, "comment": "C", "created_at": datetime(2025,1,2,9)}
        ])
        MockDBC.return_value = db
        dao = FeedbackDAO()
        lst = dao.find_by_user(7)
        assert len(lst) == 1 and lst[0].id_user == 7


def test_count_likes_dislikes():
    with patch("DAO.FeedbackDAO.DBConnection") as MockDBC:
        # likes
        db1, conn1, cur1 = make_mock_db(one={"n": 4})
        # dislikes
        db2, conn2, cur2 = make_mock_db(one={"n": 1})

        # astuce: on alterne le retour via side_effect
        MockDBC.side_effect = [db1, db2]

        dao = FeedbackDAO()
        assert dao.count_likes(42) == 4
        assert dao.count_dislikes(42) == 1
