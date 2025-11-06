import unittest
# Importation de MagicMock et patch
from unittest.mock import MagicMock, patch
from datetime import datetime

# Importations du Service et des Objets Métier
# Assurez-vous que ces chemins sont corrects dans votre environnement
from src.Service.SearchService import SearchService 
from src.Objet_Metier.Message import Message
from src.ObjetMetier.Conversation import Conversation
from src.ObjetMetier.Collaboration import Collaboration


# Définition des chemins vers les classes DAO (C'est le chemin que le SearchService utilise pour importer)
# Si SearchService importe directement les DAO depuis src.DAO, vous devez adapter ces chemins.
# Je suppose ici que SearchService les importe directement.
PATH_COLLABORATION_DAO = 'src.Service.SearchService.CollaborationDAO'
PATH_MESSAGE_DAO = 'src.Service.SearchService.MessageDAO'
PATH_CONVERSATION_DAO = 'src.Service.SearchService.ConversationDAO'


class TestSearchService:
    """Tests unitaires pour la logique du SearchService, basés sur la méthode d'injection par patch."""

    # Données de test réutilisables
    USER_ID = 42
    KEYWORD = "architecture"
    TARGET_DATE = datetime(2025, 11, 5)
    
    # IDs de conversation que l'utilisateur est censé pouvoir voir (admin, writer, viewer)
    CONV_IDS_AUTORISES = [101, 102, 103]
    COLLABORATIONS_MOCK = [
        Collaboration(id_conversation=101, id_user=USER_ID, role="admin"),
        Collaboration(id_conversation=102, id_user=USER_ID, role="writer"),
        Collaboration(id_conversation=103, id_user=USER_ID, role="viewer"),
        Collaboration(id_conversation=104, id_user=USER_ID, role="reader") # sera ignoré si 'reader' n'a pas accès à la recherche
    ]
    
    # Mock des résultats de recherche
    MESSAGE_LIST_MOCK = [Message(id_message=1, id_conversation=101, message="Message contenant architecture")]
    CONVERSATION_LIST_MOCK = [Conversation(id_conversation=101, titre="Architecture du système")]


    # --- Test Helper pour initialisation ---

    def _get_service_and_mocks(self):
        """Initialise le service en patchant les DAOs et retourne l'instance et les mocks."""
        
        # Nous utilisons le décorateur pour le patch ici pour une isolation automatique au niveau de la classe
        # Cependant, pour être plus proche du style 'with patch' sur chaque méthode, 
        # nous allons utiliser le 'with' ci-dessous.

        mock_collab_dao = MagicMock()
        mock_message_dao = MagicMock()
        mock_conversation_dao = MagicMock()
        
        # Configuration par défaut des données de sécurité
        mock_collab_dao.find_by_user.return_value = self.COLLABORATIONS_MOCK

        search_service = SearchService(
            message_dao=mock_message_dao,
            conversation_dao=mock_conversation_dao,
            collaboration_dao=mock_collab_dao
        )
        return search_service, mock_collab_dao, mock_message_dao, mock_conversation_dao


    # ------------------------------------------------------------------ #
    # TESTS DE RECHERCHE DE MESSAGES (Logique de Sécurité/Orchestration)  #
    # ------------------------------------------------------------------ #

    def test_search_messages_by_keyword_success(self):
        """Vérifie que la recherche de messages par mot-clé appelle la sécurité puis le DAO."""
        
        # Utilisation de 'with patch' pour s'assurer que l'instance de DBConnection (et le Singleton) est mockée
        with patch(PATH_COLLABORATION_DAO, new_callable=MagicMock) as MockCollabDAO, \
             patch(PATH_MESSAGE_DAO, new_callable=MagicMock) as MockMessageDAO:

            # On simule l'injection via les instances mockées
            service, mock_collab, mock_message, _ = self._get_service_and_mocks()
            
            # Configuration pour le succès
            mock_message.search_by_keyword.return_value = self.MESSAGE_LIST_MOCK

            # Exécution
            result = service.search_messages_by_keyword(self.USER_ID, self.KEYWORD)

            # 1. Vérification de la Sécurité
            mock_collab.find_by_user.assert_called_once_with(self.USER_ID)

            # 2. Vérification de l'Orchestration (appel au DAO avec les IDs filtrés)
            mock_message.search_by_keyword.assert_called_once_with(
                self.KEYWORD, 
                self.CONV_IDS_AUTORISES
            )
            
            # 3. Vérification du Résultat
            assert result == self.MESSAGE_LIST_MOCK

    def test_search_messages_by_keyword_no_access_returns_empty(self):
        """Vérifie que le service retourne vide si CollaborationDAO ne renvoie rien."""
        
        with patch(PATH_COLLABORATION_DAO, new_callable=MagicMock) as MockCollabDAO, \
             patch(PATH_MESSAGE_DAO, new_callable=MagicMock) as MockMessageDAO:
            
            service, mock_collab, mock_message, _ = self._get_service_and_mocks()
            
            # Configuration : Bloquer l'accès
            mock_collab.find_by_user.return_value = []
            
            # Exécution
            result = service.search_messages_by_keyword(self.USER_ID, self.KEYWORD)
            
            # 1. Vérification du résultat
            assert result == []
            
            # 2. Véfirication de la Sécurité : MessageDAO NE DOIT PAS être appelé
            mock_message.search_by_keyword.assert_not_called()

    def test_search_messages_by_date_success(self):
        """Vérifie le flux de recherche de messages par date."""
        
        with patch(PATH_COLLABORATION_DAO, new_callable=MagicMock) as MockCollabDAO, \
             patch(PATH_MESSAGE_DAO, new_callable=MagicMock) as MockMessageDAO:

            service, mock_collab, mock_message, _ = self._get_service_and_mocks()
            
            mock_message.search_by_date.return_value = self.MESSAGE_LIST_MOCK

            # Exécution
            service.search_messages_by_date(self.USER_ID, self.TARGET_DATE)
            
            # Vérification de l'Orchestration
            mock_message.search_by_date.assert_called_once_with(
                self.TARGET_DATE, 
                self.CONV_IDS_AUTORISES
            )

    # ---------------------------------------------------------------------- #
    # TESTS DE RECHERCHE DE CONVERSATIONS (Logique de Délégation Simple)     #
    # ---------------------------------------------------------------------- #

    def test_search_conversations_by_keyword_delegation(self):
        """Vérifie que la recherche par titre délègue directement à ConversationDAO."""
        
        with patch(PATH_CONVERSATION_DAO, new_callable=MagicMock) as MockConvDAO:
            
            # Simuler l'injection de MockConvDAO dans l'initialisation du service
            service = SearchService(MagicMock(), MockConvDAO.return_value, MagicMock())
            
            # Configuration spécifique du mock de ConversationDAO
            MockConvDAO.return_value.search_conversations_by_title.return_value = self.CONVERSATION_LIST_MOCK
            
            # Exécution du service
            result = service.search_conversations_by_keyword(self.USER_ID, self.KEYWORD)
            
            # 1. Vérification de la Délégation
            MockConvDAO.return_value.search_conversations_by_title.assert_called_once_with(
                self.USER_ID, 
                self.KEYWORD
            )
            
            # 2. Vérification du Résultat
            assert result == self.CONVERSATION_LIST_MOCK

    def test_search_conversations_by_date_delegation(self):
        """Vérifie que la recherche par date délègue directement à ConversationDAO."""
        
        with patch(PATH_CONVERSATION_DAO, new_callable=MagicMock) as MockConvDAO:
            
            # Simuler l'injection de MockConvDAO dans l'initialisation du service
            service = SearchService(MagicMock(), MockConvDAO.return_value, MagicMock())
            
            # Configuration spécifique du mock de ConversationDAO
            MockConvDAO.return_value.get_conversations_by_date.return_value = self.CONVERSATION_LIST_MOCK
            
            # Exécution du service
            result = service.search_conversations_by_date(self.USER_ID, self.TARGET_DATE)
            
            # 1. Vérification de la Délégation
            MockConvDAO.return_value.get_conversations_by_date.assert_called_once_with(
                self.USER_ID, 
                self.TARGET_DATE
            )
            
            # 2. Vérification du Résultat
            assert result == self.CONVERSATION_LIST_MOCK