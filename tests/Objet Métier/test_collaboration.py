import pytest
from src.Objet_Metier.Collaboration import Collaboration

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

def test_collaboration_edge_cases():
    # Test avec des valeurs minimales valides
    collab_min = Collaboration(id_collaboration=1, id_conversation=1, id_user=1, role="viewer")
    assert collab_min.id_collaboration == 1
    assert collab_min.id_conversation == 1
    assert collab_min.id_user == 1
    assert collab_min.role == "viewer"

    # Test avec des valeurs maximales
    max_int = 2**31 - 1
    collab_max = Collaboration(id_collaboration=max_int, id_conversation=max_int, id_user=max_int, role="admin")
    assert collab_max.id_collaboration == max_int
    assert collab_max.id_conversation == max_int
    assert collab_max.id_user == max_int
    assert collab_max.role == "admin"

    # Test avec différents rôles valides
    for valid_role in ["admin", "viewer", "writer", "banned"]:
        collab = Collaboration(id_collaboration=1, id_conversation=1, id_user=1, role=valid_role)
        assert collab.role == valid_role

def test_invalid_role():
    with pytest.raises(ValueError):
        Collaboration(id_collaboration=1, id_conversation=10, id_user=100, role="invalid_role")

def test_non_integer_ids():
    with pytest.raises(ValueError):
        Collaboration(id_collaboration=1.5, id_conversation=10, id_user=100, role="admin")
    with pytest.raises(ValueError):
        Collaboration(id_collaboration=1, id_conversation=[10], id_user=100, role="admin")
    with pytest.raises(ValueError):
        Collaboration(id_collaboration=1, id_conversation=10, id_user={"id": 100}, role="admin")

def test_none_parameters():
    with pytest.raises(ValueError):
        Collaboration(id_collaboration=None, id_conversation=10, id_user=100, role="admin")
    with pytest.raises(ValueError):
        Collaboration(id_collaboration=1, id_conversation=None, id_user=100, role="admin")
    with pytest.raises(ValueError):
        Collaboration(id_collaboration=1, id_conversation=10, id_user=None, role="admin")
    with pytest.raises(ValueError):
        Collaboration(id_collaboration=1, id_conversation=10, id_user=100, role=None)

def test_large_number_of_collaborations():
    collaborations = []
    for i in range(1000):
        collab = Collaboration(id_collaboration=i, id_conversation=i%10, id_user=i%100, role="viewer")
        collaborations.append(collab)
    assert len(collaborations) == 1000
    for i in range(1000):
        assert collaborations[i].id_collaboration == i
        assert collaborations[i].id_conversation == i % 10
        assert collaborations[i].id_user == i % 100
        assert collaborations[i].role == "viewer"

def test_role_case_sensitivity():
    with pytest.raises(ValueError):
        Collaboration(id_collaboration=1, id_conversation=10, id_user=100, role="Admin")
    with pytest.raises(ValueError):
        Collaboration(id_collaboration=1, id_conversation=10, id_user=100, role="VIEWER")
    with pytest.raises(ValueError):
        Collaboration(id_collaboration=1, id_conversation=10, id_user=100, role="Writer")

def test_whitespace_in_role():
    with pytest.raises(ValueError):
        Collaboration(id_collaboration=1, id_conversation=10, id_user=100, role=" admin ")
    with pytest.raises(ValueError):
        Collaboration(id_collaboration=1, id_conversation=10, id_user=100, role="viewer\t")
    with pytest.raises(ValueError):
        Collaboration(id_collaboration=1, id_conversation=10, id_user=100, role="\nwriter")
