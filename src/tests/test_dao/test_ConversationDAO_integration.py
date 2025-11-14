import re
from datetime import datetime
import pytest

from DAO.DBConnector import DBConnection
from DAO.ConversationDAO import ConversationDAO
from ObjetMetier.Conversation import Conversation


# ---------- Helpers infra ----------

def _row_get(row, key, idx=0):
    """
    Récupère une valeur d'une ligne retournée par psycopg2 :
    - si row est un dict-like: row[key]
    - sinon suppose un tuple et prend l'index idx
    """
    if row is None:
        return None
    if isinstance(row, dict):
        return row[key]
    return row[idx]


def _ensure_temp_user(email: str) -> int:
    """
    Crée (ou récupère) un utilisateur minimal pour satisfaire la FK collaboration.id_user.
    Détecte dynamiquement les colonnes NOT NULL sans default et fournit une valeur factice.
    """
    with DBConnection().connection as c:
        with c.cursor() as cur:
            # Déjà présent ?
            cur.execute("SELECT id_user FROM users WHERE mail=%s LIMIT 1;", (email,))
            r = cur.fetchone()
            if r:
                return _row_get(r, "id_user", 0)

            # Schéma de la table
            cur.execute("""
                SELECT column_name, is_nullable, data_type, column_default
                FROM information_schema.columns
                WHERE table_name = 'users'
            """)
            cols_info = [{
                "name": (row["column_name"] if isinstance(row, dict) else row[0]),
                "nullable": (row["is_nullable"] if isinstance(row, dict) else row[1]),
                "dtype": (row["data_type"] if isinstance(row, dict) else row[2]),
                "default": (row["column_default"] if isinstance(row, dict) else row[3]),
            } for row in cur.fetchall()]

            # Colonnes à ignorer (PK/identité auto)
            ignore_cols = {"id_user"}

            insert_cols = []
            placeholders = []
            params = []

            def add_val(col, val, use_param=True):
                insert_cols.append(col)
                if use_param:
                    placeholders.append("%s")
                    params.append(val)
                else:
                    placeholders.append(val)  # ex: NOW(), CURRENT_DATE

            # Toujours essayer de mettre des valeurs pour ces colonnes si elles existent
            present = {ci["name"].lower(): ci for ci in cols_info}
            if "mail" in present:
                add_val("mail", email)
            if "username" in present:
                add_val("username", "it_user_conversationdao")

            # Pour chaque colonne NOT NULL sans default → fournir une valeur
            for ci in cols_info:
                name = ci["name"]
                lname = name.lower()
                if lname in ignore_cols:
                    continue
                # déjà couvert par mail/username ci-dessus
                if lname in {"mail", "username"}:
                    continue

                not_null = (ci["nullable"] == "NO")
                has_default = (ci["default"] is not None)

                if not_null and not has_default:
                    # Fournir une valeur selon le type
                    dt = (ci["dtype"] or "").lower()

                    if dt in ("character varying", "text", "varchar", "citext"):
                        fake = "x" if lname != "nom" else "Doe"
                        add_val(name, fake)

                    elif dt in ("boolean",):
                        add_val(name, True)

                    elif dt in ("integer", "bigint", "smallint", "numeric", "double precision", "real", "decimal"):
                        add_val(name, 0)

                    elif dt in ("date",):
                        add_val(name, "CURRENT_DATE", use_param=False)

                    elif "timestamp" in dt:
                        add_val(name, "NOW()", use_param=False)

                    else:
                        # fallback: texte
                        add_val(name, "x")

            if not insert_cols:
                raise RuntimeError(
                    "Impossible d'insérer dans 'users' : aucune colonne insérable détectée."
                )

            cols_sql = ", ".join(insert_cols)
            vals_sql = ", ".join(placeholders)
            sql = f"INSERT INTO users ({cols_sql}) VALUES ({vals_sql}) RETURNING id_user;"
            cur.execute(sql, tuple(params))
            new_id = cur.fetchone()

        c.commit()
        return _row_get(new_id, "id_user", 0)


def _delete_temp_user(user_id: int):
    """Supprime l'utilisateur temporaire créé pour les tests (ignore si déjà supprimé)."""
    try:
        with DBConnection().connection as c:
            with c.cursor() as cur:
                cur.execute("DELETE FROM users WHERE id_user=%s;", (user_id,))
            c.commit()
    except Exception:
        # on ignore toute erreur de nettoyage
        pass


# ---------- Fixtures présence des tables ----------

@pytest.fixture(scope="module")
def has_table_conversation():
    try:
        with DBConnection().connection as c:
            with c.cursor() as cur:
                cur.execute("""
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_name = 'conversation'
                    LIMIT 1;
                """)
                return cur.fetchone() is not None
    except Exception:
        return False


@pytest.fixture(scope="module")
def has_table_collaboration():
    try:
        with DBConnection().connection as c:
            with c.cursor() as cur:
                cur.execute("""
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_name = 'collaboration'
                    LIMIT 1;
                """)
                return cur.fetchone() is not None
    except Exception:
        return False


# ---------- Tests ----------

@pytest.mark.integration
def test_crud_conversation_end_to_end(has_table_conversation):
    if not has_table_conversation:
        pytest.skip("Table 'conversation' absente — on skip le test d'intégration CRUD.")

    dao = ConversationDAO()

    # CREATE
    conv = Conversation(
        id_conversation=None,
        titre="IT - CRUD",
        created_at=datetime.now(),
        setting_conversation="{}",
        token_viewer=None,   # généré en DAO
        token_writter=None,  # généré en DAO
        is_active=True,
    )
    conv = dao.create(conv)

    assert isinstance(conv.id_conversation, int)
    assert conv.created_at is not None
    assert re.fullmatch(r"[0-9a-f]{32}", conv.token_viewer)
    assert re.fullmatch(r"[0-9a-f]{32}", conv.token_writter)

    # READ
    got = dao.read(conv.id_conversation)
    assert got is not None and got.titre == "IT - CRUD" and got.is_active is True

    # UPDATE
    assert dao.update_title(conv.id_conversation, "IT - CRUD (mod)") is True
    got2 = dao.read(conv.id_conversation)
    assert got2.titre == "IT - CRUD (mod)"

    # SET ACTIVE
    assert dao.set_active(conv.id_conversation, False) is True
    got3 = dao.read(conv.id_conversation)
    assert got3.is_active is False

    # DELETE
    assert dao.delete(conv.id_conversation) is True
    assert dao.read(conv.id_conversation) is None


@pytest.mark.integration
def test_lists_and_search_with_collaboration(has_table_conversation, has_table_collaboration):
    if not (has_table_conversation and has_table_collaboration):
        pytest.skip("Tables 'conversation' ou 'collaboration' absentes — on skip.")

    dao = ConversationDAO()

    # --- créer un user réel pour satisfaire la FK collaboration.id_user ---
    user_id = _ensure_temp_user("it_user_collab_conversationdao@example.com")

    # conversations à nettoyer in fine
    c1 = c2 = None
    try:
        # Prépare 2 conversations
        c1 = dao.create(Conversation(None, "Titre user A", datetime.now(), "{}", None, None, True))
        c2 = dao.create(Conversation(None, "Autre titre user B", datetime.now(), "{}", None, None, True))

        # Donne des accès (écritures pour c1, lecture pour c2)
        dao.add_user_access(c1.id_conversation, user_id, can_write=True)
        dao.add_user_access(c2.id_conversation, user_id, can_write=False)

        # get_conversations_by_user
        lst = dao.get_conversations_by_user(user_id)
        ids = {x.id_conversation for x in lst}
        assert c1.id_conversation in ids and c2.id_conversation in ids

        # search_conversations_by_title
        lst2 = dao.search_conversations_by_title(user_id, "titre")
        ids2 = {x.id_conversation for x in lst2}
        assert (c1.id_conversation in ids2) or (c2.id_conversation in ids2)
    finally:
        # Nettoyage
        if c1 is not None:
            try:
                dao.delete(c1.id_conversation)
            except Exception:
                pass
        if c2 is not None:
            try:
                dao.delete(c2.id_conversation)
            except Exception:
                pass
        _delete_temp_user(user_id)
