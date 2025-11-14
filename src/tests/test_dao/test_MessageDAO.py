import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

from DAO.MessageDAO import MessageDAO
from ObjetMetier.Message import Message


class TestMessageDAOUnit(unittest.TestCase):
    def setUp(self):
        self.dao = MessageDAO()

    # --- Helpers pour fabriquer un faux curseur/connexion ---

    def _mk_conn_cursor(self, fetchone_ret=None, fetchall_ret=None, rowcount=1):
        """
        Crée un faux (connection, cursor) avec contexte (with ... as ...)
        fetchone_ret: valeur renvoyée par fetchone()
        fetchall_ret: valeur renvoyée par fetchall()
        """
        fake_cursor = MagicMock()
        fake_cursor.fetchone.return_value = fetchone_ret
        fake_cursor.fetchall.return_value = fetchall_ret
        fake_cursor.rowcount = rowcount

        fake_conn_ctx = MagicMock()
        fake_conn_ctx.__enter__.return_value = fake_cursor
        fake_conn_ctx.__exit__.return_value = None

        fake_conn = MagicMock()
        fake_conn.cursor.return_value = fake_conn_ctx

        fake_conn_mgr = MagicMock()
        fake_conn_mgr.__enter__.return_value = fake_conn
        fake_conn_mgr.__exit__.return_value = None
        return fake_conn_mgr, fake_conn, fake_cursor

    # --- CREATE ---

    @patch("DAO.MessageDAO.DBConnection")
    def test_create_ok(self, MockDBC):
        row = {"id_message": 123}
        conn_mgr, _, cur = self._mk_conn_cursor(fetchone_ret=row)
        MockDBC.return_value.connection = conn_mgr

        m = Message(
            id_message=None, id_conversation=1, id_user=2,
            datetime=datetime(2025, 1, 1, 10, 0, 0),
            message="hello", is_from_agent=False
        )
        out = self.dao.create(m)
        assert out.id_message == 123

        # vérifie qu'on a passé les bons params (timestamp = .datetime)
        args, kwargs = cur.execute.call_args
        assert "INSERT INTO message" in args[0]
        params = args[1]
        assert params["id_conversation"] == 1
        assert params["id_user"] == 2
        assert params["timestamp"] == datetime(2025, 1, 1, 10, 0, 0)
        assert params["message"] == "hello"
        assert params["is_from_agent"] is False

    # --- READ ---

    @patch("DAO.MessageDAO.DBConnection")
    def test_get_by_id_found(self, MockDBC):
        row = {
            "id_message": 5, "id_conversation": 1, "id_user": 2,
            "timestamp": datetime(2025, 1, 2, 12, 0, 0),
            "message": "hi", "is_from_agent": True
        }
        conn_mgr, _, _ = self._mk_conn_cursor(fetchone_ret=row)
        MockDBC.return_value.connection = conn_mgr

        m = self.dao.get_by_id(5)
        assert m is not None
        assert m.id_message == 5
        assert m.id_conversation == 1
        assert m.id_user == 2
        assert m.datetime == row["timestamp"]
        assert m.message == "hi"
        assert m.is_from_agent is True

    @patch("DAO.MessageDAO.DBConnection")
    def test_get_by_id_not_found(self, MockDBC):
        conn_mgr, _, _ = self._mk_conn_cursor(fetchone_ret=None)
        MockDBC.return_value.connection = conn_mgr
        assert self.dao.get_by_id(9999) is None

    # --- LISTING ---

    @patch("DAO.MessageDAO.DBConnection")
    def test_get_messages_by_conversation(self, MockDBC):
        rows = [
            {"id_message": 1, "id_conversation": 10, "id_user": 2, "timestamp": datetime(2025,1,1,10), "message": "a", "is_from_agent": False},
            {"id_message": 2, "id_conversation": 10, "id_user": 3, "timestamp": datetime(2025,1,1,11), "message": "b", "is_from_agent": True},
        ]
        conn_mgr, _, _ = self._mk_conn_cursor(fetchall_ret=rows)
        MockDBC.return_value.connection = conn_mgr

        msgs = self.dao.get_messages_by_conversation(10)
        assert len(msgs) == 2
        assert msgs[0].id_message == 1 and msgs[1].id_message == 2

    @patch("DAO.MessageDAO.DBConnection")
    def test_get_messages_by_conversation_paginated(self, MockDBC):
        rows = [
            {"id_message": 3, "id_conversation": 10, "id_user": 2, "timestamp": datetime(2025,1,2,10), "message": "c", "is_from_agent": False},
        ]
        conn_mgr, _, cur = self._mk_conn_cursor(fetchall_ret=rows)
        MockDBC.return_value.connection = conn_mgr

        msgs = self.dao.get_messages_by_conversation_paginated(10, page=2, per_page=1)
        assert len(msgs) == 1 and msgs[0].id_message == 3

        # vérifie LIMIT / OFFSET paramétrés
        args, kwargs = cur.execute.call_args
        params = args[1]
        assert params["limit"] == 1
        assert params["offset"] == 1  # (page-1)*per_page

    @patch("DAO.MessageDAO.DBConnection")
    def test_count_messages_by_conversation(self, MockDBC):
        conn_mgr, _, _ = self._mk_conn_cursor(fetchone_ret={"n": 42})
        MockDBC.return_value.connection = conn_mgr
        assert self.dao.count_messages_by_conversation(10) == 42

    # --- SEARCH (multi-conv) ---

    @patch("DAO.MessageDAO.DBConnection")
    def test_search_by_keyword(self, MockDBC):
        rows = [
            {"id_message": 7, "id_conversation": 101, "id_user": 2, "timestamp": datetime(2025,1,3,10), "message": "architecture", "is_from_agent": False},
        ]
        conn_mgr, _, cur = self._mk_conn_cursor(fetchall_ret=rows)
        MockDBC.return_value.connection = conn_mgr

        msgs = self.dao.search_by_keyword("arch", [101,102,103])
        assert len(msgs) == 1 and msgs[0].id_message == 7

        # Vérifie que 'ids' est bien un tuple pour l'IN
        args, kwargs = cur.execute.call_args
        params = args[1]
        assert isinstance(params["ids"], tuple)
        assert params["ids"] == (101, 102, 103)
        assert params["kw"] == "%arch%"

    @patch("DAO.MessageDAO.DBConnection")
    def test_search_by_date(self, MockDBC):
        rows = [
            {"id_message": 8, "id_conversation": 101, "id_user": 2, "timestamp": datetime(2025,1,4,18), "message": "X", "is_from_agent": False},
        ]
        conn_mgr, _, cur = self._mk_conn_cursor(fetchall_ret=rows)
        MockDBC.return_value.connection = conn_mgr

        target = datetime(2025, 1, 4)
        msgs = self.dao.search_by_date(target, [101])
        assert len(msgs) == 1 and msgs[0].id_message == 8

        args, kwargs = cur.execute.call_args
        params = args[1]
        assert params["ids"] == (101,)
        assert params["start"].date() == target.date()
        assert params["end"].date() == target.date()

    # --- RANGE / UPDATE / DELETE / LAST ---

    @patch("DAO.MessageDAO.DBConnection")
    def test_get_messages_by_date_range(self, MockDBC):
        rows = [
            {"id_message": 9, "id_conversation": 10, "id_user": 2, "timestamp": datetime(2025,1,5,9), "message": "range", "is_from_agent": False}
        ]
        conn_mgr, _, _ = self._mk_conn_cursor(fetchall_ret=rows)
        MockDBC.return_value.connection = conn_mgr

        s = datetime(2025,1,5,0,0,0)
        e = datetime(2025,1,5,23,59,59)
        msgs = self.dao.get_messages_by_date_range(10, s, e)
        assert len(msgs) == 1 and msgs[0].message == "range"

    @patch("DAO.MessageDAO.DBConnection")
    def test_update(self, MockDBC):
        conn_mgr, _, _ = self._mk_conn_cursor(rowcount=1)
        MockDBC.return_value.connection = conn_mgr

        m = Message(1, 10, 2, datetime(2025,1,6,10), "new content", False)
        assert self.dao.update(m) is True

    @patch("DAO.MessageDAO.DBConnection")
    def test_delete_by_id(self, MockDBC):
        conn_mgr, _, _ = self._mk_conn_cursor(rowcount=1)
        MockDBC.return_value.connection = conn_mgr
        assert self.dao.delete_by_id(123) is True

    @patch("DAO.MessageDAO.DBConnection")
    def test_get_last_message(self, MockDBC):
        row = {"id_message": 50, "id_conversation": 10, "id_user": 3,
               "timestamp": datetime(2025,1,7,19), "message": "last", "is_from_agent": True}
        conn_mgr, _, _ = self._mk_conn_cursor(fetchone_ret=row)
        MockDBC.return_value.connection = conn_mgr

        m = self.dao.get_last_message(10)
        assert m and m.id_message == 50 and m.message == "last"


if __name__ == "__main__":
    unittest.main()
