import pytest
from src.ObjetMetier.Collaboration import Collaboration


def test_collaboration_initialization():
    collaboration = Collaboration(
        id_collaboration=1, id_conversation=10, id_user=100, role="admin"
    )
    assert collaboration.id_collaboration == 1
    assert collaboration.id_conversation == 10
    assert collaboration.id_user == 100
    assert collaboration.role == "admin"


def test_collaboration_initialization_without_id():
    """Test qu'on peut créer une collaboration sans id_collaboration"""
    collaboration = Collaboration(
        id_collaboration=None, id_conversation=10, id_user=100, role="admin"
    )
    assert collaboration.id_collaboration is None
    assert collaboration.id_conversation == 10
    assert collaboration.id_user == 100
    assert collaboration.role == "admin"


def test_collaboration_init_type_errors():
    with pytest.raises(ValueError):
        Collaboration(
            id_collaboration="notint", id_conversation=10, id_user=100, role="admin"
        )
    with pytest.raises(ValueError):
        Collaboration(
            id_collaboration=1, id_conversation="notint", id_user=100, role="admin"
        )
    with pytest.raises(ValueError):
        Collaboration(
            id_collaboration=1, id_conversation=10, id_user="notint", role="admin"
        )
    with pytest.raises(ValueError):
        Collaboration(id_collaboration=1, id_conversation=10, id_user=100, role=123)

    # ⚠️ SUPPRIMÉ : id_collaboration=None est maintenant valide
    # with pytest.raises(ValueError):
    #     Collaboration(
    #         id_collaboration=None, id_conversation=10, id_user=100, role="admin"
    #     )

    with pytest.raises(ValueError):
        Collaboration(
            id_collaboration=1, id_conversation=None, id_user=100, role="admin"
        )
    with pytest.raises(ValueError):
        Collaboration(
            id_collaboration=1, id_conversation=10, id_user=None, role="admin"
        )
    with pytest.raises(ValueError):
        Collaboration(id_collaboration=1, id_conversation=10, id_user=100, role=None)


def test_collaboration_equality():
    collab1 = Collaboration(
        id_collaboration=1, id_conversation=10, id_user=100, role="admin"
    )
    collab2 = Collaboration(
        id_collaboration=1, id_conversation=10, id_user=100, role="admin"
    )
    collab3 = Collaboration(
        id_collaboration=2, id_conversation=20, id_user=200, role="writer"
    )

    assert collab1 == collab2
    assert collab1 != collab3


def test_collaboration_equality_with_none_id():
    """Test l'égalité avec id_collaboration=None"""
    collab1 = Collaboration(
        id_collaboration=None, id_conversation=10, id_user=100, role="admin"
    )
    collab2 = Collaboration(
        id_collaboration=None, id_conversation=10, id_user=100, role="admin"
    )
    collab3 = Collaboration(
        id_collaboration=1, id_conversation=10, id_user=100, role="admin"
    )

    assert collab1 == collab2
    assert collab1 != collab3


def test_str():
    collab = Collaboration(
        id_collaboration=1, id_conversation=10, id_user=100, role="admin"
    )
    assert (
        str(collab)
        == "Collaboration(id_collaboration=1, id_conversation=10, id_user=100, role='admin')"
    )


def test_str_with_none_id():
    """Test la représentation string avec id_collaboration=None"""
    collab = Collaboration(
        id_collaboration=None, id_conversation=10, id_user=100, role="admin"
    )
    assert (
        str(collab)
        == "Collaboration(id_collaboration=None, id_conversation=10, id_user=100, role='admin')"
    )


def test_repr():
    """Test que __repr__ retourne la même chose que __str__"""
    collab = Collaboration(
        id_collaboration=1, id_conversation=10, id_user=100, role="admin"
    )
    assert repr(collab) == str(collab)


def test_collaboration_edge_cases():
    # Test avec des valeurs minimales valides
    collab_min = Collaboration(
        id_collaboration=1, id_conversation=1, id_user=1, role="viewer"
    )
    assert collab_min.id_collaboration == 1
    assert collab_min.id_conversation == 1
    assert collab_min.id_user == 1
    assert collab_min.role == "viewer"

    # Test avec des valeurs maximales
    max_int = 2**31 - 1
    collab_max = Collaboration(
        id_collaboration=max_int, id_conversation=max_int, id_user=max_int, role="admin"
    )
    assert collab_max.id_collaboration == max_int
    assert collab_max.id_conversation == max_int
    assert collab_max.id_user == max_int
    assert collab_max.role == "admin"

    # Test avec différents rôles valides
    for valid_role in ["admin", "viewer", "writer", "banned"]:
        collab = Collaboration(
            id_collaboration=1, id_conversation=1, id_user=1, role=valid_role
        )
        assert collab.role == valid_role


def test_invalid_role():
    with pytest.raises(ValueError):
        Collaboration(
            id_collaboration=1, id_conversation=10, id_user=100, role="invalid_role"
        )


def test_non_integer_ids():
    with pytest.raises(ValueError):
        Collaboration(
            id_collaboration=1.5, id_conversation=10, id_user=100, role="admin"
        )
    with pytest.raises(ValueError):
        Collaboration(
            id_collaboration=1, id_conversation=[10], id_user=100, role="admin"
        )
    with pytest.raises(ValueError):
        Collaboration(
            id_collaboration=1, id_conversation=10, id_user={"id": 100}, role="admin"
        )


def test_none_parameters():
    # ⚠️ MODIFIÉ : id_collaboration=None est maintenant valide
    collab = Collaboration(
        id_collaboration=None, id_conversation=10, id_user=100, role="admin"
    )
    assert collab.id_collaboration is None

    # Les autres None restent invalides
    with pytest.raises(ValueError):
        Collaboration(
            id_collaboration=1, id_conversation=None, id_user=100, role="admin"
        )
    with pytest.raises(ValueError):
        Collaboration(
            id_collaboration=1, id_conversation=10, id_user=None, role="admin"
        )
    with pytest.raises(ValueError):
        Collaboration(id_collaboration=1, id_conversation=10, id_user=100, role=None)


def test_large_number_of_collaborations():
    collaborations = []
    for i in range(1000):
        collab = Collaboration(
            id_collaboration=i, id_conversation=i % 10, id_user=i % 100, role="viewer"
        )
        collaborations.append(collab)
    assert len(collaborations) == 1000
    for i in range(1000):
        assert collaborations[i].id_collaboration == i
        assert collaborations[i].id_conversation == i % 10
        assert collaborations[i].id_user == i % 100
        assert collaborations[i].role == "viewer"



def test_whitespace_in_role():
    with pytest.raises(ValueError):
        Collaboration(
            id_collaboration=1, id_conversation=10, id_user=100, role=" admin "
        )
    with pytest.raises(ValueError):
        Collaboration(
            id_collaboration=1, id_conversation=10, id_user=100, role="viewer\t"
        )
    with pytest.raises(ValueError):
        Collaboration(
            id_collaboration=1, id_conversation=10, id_user=100, role="\nwriter"
        )


def test_inequality_with_different_types():
    """Test que la comparaison avec d'autres types retourne False"""
    collab = Collaboration(
        id_collaboration=1, id_conversation=10, id_user=100, role="admin"
    )
    assert collab != "not a collaboration"
    assert collab != 123
    assert collab != None
    assert collab != {"id": 1}


def test_negative_ids():
    """Test avec des IDs négatifs (valides car ce sont des int)"""
    collab = Collaboration(
        id_collaboration=-1, id_conversation=-10, id_user=-100, role="admin"
    )
    assert collab.id_collaboration == -1
    assert collab.id_conversation == -10
    assert collab.id_user == -100


def test_zero_ids():
    """Test avec des IDs à zéro"""
    collab = Collaboration(
        id_collaboration=0, id_conversation=0, id_user=0, role="banned"
    )
    assert collab.id_collaboration == 0
    assert collab.id_conversation == 0
    assert collab.id_user == 0
    assert collab.role == "banned"

def test_role_as_empty_string():
    """Test avec un rôle comme chaîne vide"""
    with pytest.raises(ValueError):
        Collaboration(
            id_collaboration=1, id_conversation=10, id_user=100, role=""
        )

def test_role_with_special_characters():
    """Test avec des rôles contenant des caractères spéciaux"""
    with pytest.raises(ValueError):
        Collaboration(
            id_collaboration=1, id_conversation=10, id_user=100, role="adm!n"
        )
    with pytest.raises(ValueError):
        Collaboration(
            id_collaboration=1, id_conversation=10, id_user=100, role="view#er"
        )
    with pytest.raises(ValueError):
        Collaboration(
            id_collaboration=1, id_conversation=10, id_user=100, role="writ$er"
        )


def test_multiple_collaborations_equality():
    """Test l'égalité entre plusieurs collaborations dans une liste"""
    collabs1 = [
        Collaboration(id_collaboration=i, id_conversation=1, id_user=1, role="admin")
        for i in range(5)
    ]
    collabs2 = [
        Collaboration(id_collaboration=i, id_conversation=1, id_user=1, role="admin")
        for i in range(5)
    ]
    collabs3 = [
        Collaboration(id_collaboration=i + 1, id_conversation=1, id_user=1, role="admin")
        for i in range(5)
    ]

    for c1, c2 in zip(collabs1, collabs2):
        assert c1 == c2

    for c1, c3 in zip(collabs1, collabs3):
        assert c1 != c3

def test_role_with_numeric_string():
    """Test avec un rôle comme chaîne numérique"""
    with pytest.raises(ValueError):
        Collaboration(
            id_collaboration=1, id_conversation=10, id_user=100, role="123"
        )

def test_collaboration_with_special_characters_in_ids():
            """Test avec des caractères spéciaux dans les IDs"""
            with pytest.raises(ValueError):
                Collaboration(
                    id_collaboration="1!", id_conversation=10, id_user=100, role="admin"
                )
            with pytest.raises(ValueError):
                Collaboration(
                    id_collaboration=1, id_conversation="10#", id_user=100, role="admin"
                )
            with pytest.raises(ValueError):
                Collaboration(
                    id_collaboration=1, id_conversation=10, id_user="100$", role="admin"
                )

def test_collaboration_with_empty_strings_in_ids():
            """Test avec des chaînes vides dans les IDs"""
            with pytest.raises(ValueError):
                Collaboration(
                    id_collaboration="", id_conversation=10, id_user=100, role="admin"
                )
            with pytest.raises(ValueError):
                Collaboration(
                    id_collaboration=1, id_conversation="", id_user=100, role="admin"
                )
            with pytest.raises(ValueError):
                Collaboration(
                    id_collaboration=1, id_conversation=10, id_user="", role="admin"
                )

def test_collaboration_with_whitespace_in_ids():
            """Test avec des espaces dans les IDs"""
            with pytest.raises(ValueError):
                Collaboration(
                    id_collaboration=" 1", id_conversation=10, id_user=100, role="admin"
                )
            with pytest.raises(ValueError):
                Collaboration(
                    id_collaboration=1, id_conversation="10 ", id_user=100, role="admin"
                )
            with pytest.raises(ValueError):
                Collaboration(
                    id_collaboration=1, id_conversation=10, id_user=" 100 ", role="admin"
                )

def test_collaboration_with_large_ids():
            """Test avec des IDs très grands"""
            large_id = 10**18
            collab = Collaboration(
                id_collaboration=large_id, id_conversation=large_id, id_user=large_id, role="admin"
            )
            assert collab.id_collaboration == large_id
            assert collab.id_conversation == large_id
            assert collab.id_user == large_id

def test_collaboration_with_negative_and_zero_combination():
            """Test avec une combinaison d'IDs négatifs et zéro"""
            collab = Collaboration(
                id_collaboration=-1, id_conversation=0, id_user=-100, role="viewer"
            )
            assert collab.id_collaboration == -1
            assert collab.id_conversation == 0
            assert collab.id_user == -100
            assert collab.role == "viewer"

def test_collaboration_with_non_ascii_role():
            """Test avec un rôle contenant des caractères non-ASCII"""
            with pytest.raises(ValueError):
                Collaboration(
                    id_collaboration=1, id_conversation=10, id_user=100, role="administrateur"
                )
            with pytest.raises(ValueError):
                Collaboration(
                    id_collaboration=1, id_conversation=10, id_user=100, role="观众"
                )

def test_collaboration_with_duplicate_objects():
            """Test que deux objets identiques sont égaux"""
            collab1 = Collaboration(
                id_collaboration=1, id_conversation=10, id_user=100, role="admin"
            )
            collab2 = Collaboration(
                id_collaboration=1, id_conversation=10, id_user=100, role="admin"
            )
            assert collab1 == collab2

def test_collaboration_with_different_roles():
            """Test que deux collaborations avec des rôles différents ne sont pas égales"""
            collab1 = Collaboration(
                id_collaboration=1, id_conversation=10, id_user=100, role="admin"
            )
            collab2 = Collaboration(
                id_collaboration=1, id_conversation=10, id_user=100, role="viewer"
            )
            assert collab1 != collab2

def test_collaboration_with_partial_none_ids():
            """Test avec certains IDs à None"""
            with pytest.raises(ValueError):
                Collaboration(
                    id_collaboration=None, id_conversation=None, id_user=100, role="admin"
                )
            with pytest.raises(ValueError):
                Collaboration(
                    id_collaboration=1, id_conversation=None, id_user=None, role="admin"
                )
