import pytest
from src.Model.Collaboration import Collaboration

def test_collaboration_initialization():
    collaboration = Collaboration(
        id_collaboration=1,
        id_conversation=10,
        id_user=100,
        role="admin"
    )
    assert collaboration.id_collaboration == 1
    assert collaboration.id_conversation == 10
    assert collaboration.id_user == 100
    assert collaboration.role == "admin"

def test_collaboration_init_type_errors():
    with pytest.raises(ValueError):
        Collaboration(id_collaboration="notint", id_conversation=10, id_user=100, role="admin")
    with pytest.raises(ValueError):
        Collaboration(id_collaboration=1, id_conversation="notint", id_user=100, role="admin")
    with pytest.raises(ValueError):
        Collaboration(id_collaboration=1, id_conversation=10, id_user="notint", role="admin")
    with pytest.raises(ValueError):
        Collaboration(id_collaboration=1, id_conversation=10, id_user=100, role=123)
    with pytest.raises(ValueError):
        Collaboration(id_collaboration=None, id_conversation=10, id_user=100, role="admin")
    with pytest.raises(ValueError):
        Collaboration(id_collaboration=1, id_conversation=None, id_user=100, role="admin")
    with pytest.raises(ValueError):
        Collaboration(id_collaboration=1, id_conversation=10, id_user=None, role="admin")
    with pytest.raises(ValueError):
        Collaboration(id_collaboration=1, id_conversation=10, id_user=100, role=None)

def test_collaboration_equality():
    collab1 = Collaboration(id_collaboration=1, id_conversation=10, id_user=100, role="admin")
    collab2 = Collaboration(id_collaboration=1, id_conversation=10, id_user=100, role="admin")
    collab3 = Collaboration(id_collaboration=2, id_conversation=20, id_user=200, role="writer")

    assert collab1 == collab2
    assert collab1 != collab3

def test_str():
    collab = Collaboration(id_collaboration=1, id_conversation=10, id_user=100, role="admin")
    assert str(collab) == "Collaboration(id_collaboration=1, id_conversation=10, id_user=100, role='admin')"
