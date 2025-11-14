import datetime
from types import SimpleNamespace
from unittest.mock import Mock
import pytest

from Service.StatisticsService import StatisticsService

T0 = datetime.datetime(2025, 1, 1, 10, 0, 0)

def msg(mins, conv, user, text="x", *, with_dt=True):
    return SimpleNamespace(
        id_message=None,
        id_conversation=conv,
        id_user=user,
        datetime=(T0 + datetime.timedelta(minutes=mins)) if with_dt else None,
        message=text,
        is_from_agent=False,
    )

def test_nb_conv_prefers_count_then_fallback_list_len_set():
    collaboration_dao = Mock()
    collaboration_dao.count_conversations_by_user.return_value = 3
    message_dao = Mock()
    svc = StatisticsService(message_dao=message_dao, collaboration_dao=collaboration_dao)
    assert svc.nb_conv(7) == 3
    collaboration_dao.count_conversations_by_user.assert_called_once_with(7)

    collaboration_dao = Mock()
    collaboration_dao.count_conversations_by_user = None
    collaboration_dao.count_by_user = None
    collaboration_dao.count_conv_by_user = None
    collaboration_dao.get_by_user_id.return_value = [
        SimpleNamespace(id_conversation=10, id_user=7),
        SimpleNamespace(id_conversation=11, id_user=7),
        SimpleNamespace(id_conversation=11, id_user=7),
    ]
    svc = StatisticsService(message_dao=message_dao, collaboration_dao=collaboration_dao)
    assert svc.nb_conv(7) == 2
    collaboration_dao.get_by_user_id.assert_called_once_with(7)

def test_nb_conv_fallback_messages_when_no_collab():
    message_dao = Mock()
    message_dao.get_messages_by_user.return_value = [
        msg(0, 10, 1),
        msg(1, 11, 1),
        msg(2, 11, 2),
    ]
    svc = StatisticsService(message_dao=message_dao, collaboration_dao=None)
    assert svc.nb_conv(1) == 2
    message_dao.get_messages_by_user.assert_called_once_with(1)

def test_nb_conv_raises_when_no_compatible_methods():
    message_dao = Mock()
    for name in ["get_messages_by_user", "get_by_user", "get_messages_for_user"]:
        setattr(message_dao, name, None)
    svc = StatisticsService(message_dao=message_dao, collaboration_dao=None)
    with pytest.raises(RuntimeError):
        svc.nb_conv(1)

def test_nb_messages_uses_count_then_fallback_get():
    message_dao = Mock()
    message_dao.count_messages_by_user.return_value = 5
    svc = StatisticsService(message_dao=message_dao)
    assert svc.nb_messages(9) == 5
    message_dao.count_messages_by_user.assert_called_once_with(9)

    message_dao = Mock()
    message_dao.count_messages_by_user = None
    message_dao.count_by_user = None
    message_dao.get_messages_by_user.return_value = [msg(0, 1, 9), msg(1, 2, 9)]
    svc = StatisticsService(message_dao=message_dao)
    assert svc.nb_messages(9) == 2
    message_dao.get_messages_by_user.assert_called_once_with(9)

def test_nb_messages_raises_when_no_methods():
    message_dao = Mock()
    for name in ["count_messages_by_user", "count_by_user",
                 "get_messages_by_user", "get_by_user", "get_messages_for_user"]:
        setattr(message_dao, name, None)
    svc = StatisticsService(message_dao=message_dao)
    with pytest.raises(RuntimeError):
        svc.nb_messages(1)

def test_nb_message_conv_uses_count_then_fallback_get():
    message_dao = Mock()
    message_dao.count_messages_by_conversation.return_value = 7
    svc = StatisticsService(message_dao=message_dao)
    assert svc.nb_message_conv(42) == 7
    message_dao.count_messages_by_conversation.assert_called_once_with(42)

    message_dao = Mock()
    message_dao.count_messages_by_conversation = None
    message_dao.count_by_conversation = None
    message_dao.get_messages_by_conversation.return_value = [msg(0, 42, 1)] * 3
    svc = StatisticsService(message_dao=message_dao)
    assert svc.nb_message_conv(42) == 3
    message_dao.get_messages_by_conversation.assert_called_once_with(42)

def test_nb_message_conv_raises_when_no_methods():
    message_dao = Mock()
    for name in ["count_messages_by_conversation", "count_by_conversation",
                 "get_messages_by_conversation", "get_by_conversation"]:
        setattr(message_dao, name, None)
    svc = StatisticsService(message_dao=message_dao)
    with pytest.raises(RuntimeError):
        svc.nb_message_conv(1)

def test_nb_messages_de_user_par_conv_all_paths_and_raises():
    message_dao = Mock()
    message_dao.count_messages_user_in_conversation.return_value = 4
    svc = StatisticsService(message_dao=message_dao)
    assert svc.nb_messages_de_user_par_conv(7, 10) == 4
    message_dao.count_messages_user_in_conversation.assert_called_once_with(7, 10)

    message_dao = Mock()
    message_dao.count_messages_user_in_conversation = None
    message_dao.count_by_user_in_conversation = None
    message_dao.get_by_conversation_and_user = None
    message_dao.get_messages_by_conversation_and_user.return_value = [msg(0, 10, 7)] * 3
    svc = StatisticsService(message_dao=message_dao)
    assert svc.nb_messages_de_user_par_conv(7, 10) == 3
    message_dao.get_messages_by_conversation_and_user.assert_called_once_with(10, 7)

    message_dao = Mock()
    message_dao.count_messages_user_in_conversation = None
    message_dao.count_by_user_in_conversation = None
    message_dao.get_messages_by_conversation_and_user = None
    message_dao.get_by_conversation_and_user = None
    message_dao.get_messages_by_conversation.return_value = [
        msg(0, 10, 7), msg(1, 10, 8), msg(2, 10, 7)
    ]
    svc = StatisticsService(message_dao=message_dao)
    assert svc.nb_messages_de_user_par_conv(7, 10) == 2
    message_dao.get_messages_by_conversation.assert_called_once_with(10)

    message_dao = Mock()
    for name in ["count_messages_user_in_conversation", "count_by_user_in_conversation",
                 "get_messages_by_conversation_and_user", "get_by_conversation_and_user",
                 "get_messages_by_conversation", "get_by_conversation"]:
        setattr(message_dao, name, None)
    svc = StatisticsService(message_dao=message_dao)
    with pytest.raises(RuntimeError):
        svc.nb_messages_de_user_par_conv(7, 10)

def test_temps_passe_simple_window_uses_helper():
    svc = StatisticsService(message_dao=Mock())
    svc._get_sorted_timestamps_for_user = Mock(return_value=[T0, T0 + datetime.timedelta(minutes=60)])
    assert svc.temps_passe(1, simple_window=True) == datetime.timedelta(minutes=60)
    svc._get_sorted_timestamps_for_user.assert_called_once_with(1)

def test_temps_passe_sums_sessions_by_conv_with_threshold():
    svc = StatisticsService(message_dao=Mock(), idle_threshold=datetime.timedelta(minutes=10))
    svc._get_conversation_ids_of_user = Mock(return_value=[10, 20])
    svc._get_sorted_timestamps_for_user_in_conv = Mock(side_effect=[
        [T0, T0 + datetime.timedelta(minutes=5), T0 + datetime.timedelta(minutes=9),
         T0 + datetime.timedelta(minutes=40), T0 + datetime.timedelta(minutes=50)],
        [T0 + datetime.timedelta(minutes=60)]
    ])
    assert svc.temps_passe(1) == datetime.timedelta(minutes=19)

def test_temps_passe_fallback_to_global_when_no_conversations():
    svc = StatisticsService(message_dao=Mock(), idle_threshold=datetime.timedelta(minutes=10))
    svc._get_conversation_ids_of_user = Mock(return_value=[])
    svc._get_sorted_timestamps_for_user = Mock(
        return_value=[T0, T0 + datetime.timedelta(minutes=5), T0 + datetime.timedelta(minutes=30)]
    )
    assert svc.temps_passe(1) == datetime.timedelta(minutes=5)

def test_temps_passe_par_conv_paths_simple_and_sessions():
    svc = StatisticsService(message_dao=Mock(), idle_threshold=datetime.timedelta(minutes=10))
    svc._get_sorted_timestamps_for_user_in_conv = Mock(
        return_value=[T0, T0 + datetime.timedelta(minutes=9), T0 + datetime.timedelta(minutes=25)]
    )
    assert svc.temps_passe_par_conv(1, 10) == datetime.timedelta(minutes=9)
    svc._get_sorted_timestamps_for_user_in_conv.return_value = [T0, T0 + datetime.timedelta(minutes=60)]
    assert svc.temps_passe_par_conv(1, 10, simple_window=True) == datetime.timedelta(minutes=60)

def test_top_active_users_direct_and_fallback_and_validation():
    message_dao = Mock()
    message_dao.get_top_users_by_message_count.return_value = [
        (3, 10),
        {"user_id": 2, "count": 7},
        (5, 1, "extra"),
    ]
    svc = StatisticsService(message_dao=message_dao)
    assert svc.top_active_users(limit=3) == [(3, 10), (2, 7), (5, 1)]

    messages = [msg(0, 1, 7), msg(1, 2, 7), msg(2, 2, 8), msg(3, 2, 7)]
    message_dao = Mock()
    message_dao.get_top_users_by_message_count = None
    message_dao.top_users = None
    message_dao.get_all_messages = None
    message_dao.get_all = None
    message_dao.get_all_messages_minimal.return_value = messages
    svc = StatisticsService(message_dao=message_dao)
    assert svc.top_active_users(limit=2) == [(7, 3), (8, 1)]

    with pytest.raises(ValueError):
        svc.top_active_users(limit=0)

    message_dao = Mock()
    message_dao.get_top_users_by_message_count = None
    message_dao.top_users = None
    message_dao.get_all_messages_minimal = None
    message_dao.get_all_messages = None
    message_dao.get_all = None
    with pytest.raises(RuntimeError):
        StatisticsService(message_dao=message_dao).top_active_users(limit=1)

def test_average_message_length_direct_then_fallback_and_empty():
    message_dao = Mock()
    message_dao.get_average_message_length.return_value = 12.5
    svc = StatisticsService(message_dao=message_dao)
    assert svc.average_message_length() == pytest.approx(12.5)

    messages = [msg(0, 1, 7, "aa"), msg(1, 1, 7, "bbbb")]
    message_dao = Mock()
    message_dao.get_average_message_length.side_effect = RuntimeError("boom")
    message_dao.get_all_messages_minimal.return_value = messages
    svc = StatisticsService(message_dao=message_dao)
    assert svc.average_message_length() == pytest.approx(3.0)

    message_dao = Mock()
    message_dao.get_average_message_length.side_effect = RuntimeError("boom")
    message_dao.get_all_messages_minimal.return_value = []
    svc = StatisticsService(message_dao=message_dao)
    assert svc.average_message_length() == 0.0

def test_get_sorted_timestamps_for_user_filters_none_and_sorts():
    mdao = Mock()
    mdao.get_messages_by_user.return_value = [
        msg(5, 10, 7),
        msg(0, 10, 7),
        msg(9, 10, 7, with_dt=False),
        SimpleNamespace(id_conversation=10, id_user=7, message="x"),
    ]
    svc = StatisticsService(message_dao=mdao)
    ts = svc._get_sorted_timestamps_for_user(7)
    assert ts == [T0, T0 + datetime.timedelta(minutes=5)]

def test_get_sorted_timestamps_for_user_in_conv_filters_and_orders_both_paths():
    mdao = Mock()
    mdao.get_messages_by_conversation_and_user.return_value = [
        msg(9, 10, 7),
        msg(0, 10, 7),
        msg(5, 10, 7, with_dt=False),
    ]
    svc = StatisticsService(message_dao=mdao)
    ts = svc._get_sorted_timestamps_for_user_in_conv(7, 10)
    assert ts == [T0, T0 + datetime.timedelta(minutes=9)]

    mdao = Mock()
    mdao.get_messages_by_conversation_and_user = None
    mdao.get_by_conversation_and_user = None
    mdao.get_messages_by_conversation.return_value = [
        msg(5, 10, 7),
        msg(0, 10, 7),
        msg(2, 10, 8),
    ]
    svc = StatisticsService(message_dao=mdao)
    ts2 = svc._get_sorted_timestamps_for_user_in_conv(7, 10)
    assert ts2 == [T0, T0 + datetime.timedelta(minutes=5)]

def test_get_conversation_ids_via_conversation_dao_then_messages_fallback():
    conversation_dao = Mock()
    conversation_dao.get_list_conv.return_value = [
        SimpleNamespace(id_conversation=10),
        SimpleNamespace(id_conversation=20),
        SimpleNamespace(id_conversation=20),
    ]
    svc = StatisticsService(message_dao=Mock(), conversation_dao=conversation_dao)
    ids = svc._get_conversation_ids_of_user(123)
    assert ids == [10, 20]
    conversation_dao.get_list_conv.assert_called_once_with(123)

    message_dao = Mock()
    message_dao.get_messages_by_user.return_value = [msg(0, 5, 1), msg(1, 5, 1), msg(2, 7, 1)]
    svc = StatisticsService(message_dao=message_dao, conversation_dao=None, collaboration_dao=None)
    ids2 = svc._get_conversation_ids_of_user(1)
    assert set(ids2) == {5, 7}
