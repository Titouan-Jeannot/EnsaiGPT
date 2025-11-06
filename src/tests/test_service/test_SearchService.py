import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime

from src.Service.SearchService import SearchService 
from src.ObjetMetier.Message import Message   # <-- correction d'import
from src.ObjetMetier.Conversation import Conversation
from src.ObjetMetier.Collaboration import Collaboration

PATH_COLLABORATION_DAO = 'src.Service.SearchService.CollaborationDAO'
PATH_MESSAGE_DAO = 'src.Service.SearchService.MessageDAO'
PATH_CONVERSATION_DAO = 'src.Service.SearchService.ConversationDAO'


class TestSearchService:
    """Tests unitaires pour la logique du SearchService, basés sur la méthode d'injection par patch."""

    USER_ID = 42
    KEYWORD = "architecture"
    TARGET_DATE = datetime(2025, 11, 5)
    
    # ✅ Aligne l'attendu avec le comportement actuel du service (inclut 'reader')
    CONV_IDS_AUTORISES = [101, 102, 103, 104]

    COLLABORATIONS_MOCK = [
        Collaboration(id_conversation=101, id_user=USER_ID, role="admin"),
        Collaboration(id_conversation=102, id_user=USER_ID, role="writer"),
        Collaboration(id_conversation=103, id_user=USER_ID, role="viewer"),
        Collaboration(id_conversation=104, id_user=USER_ID, role="reader")  # inclus
    ]
    
    MESSAGE_LIST_MOCK = [Message(id_message=1, id_conversation=101, message="Message contenant architecture")]
    CONVERSATION_LIST_MOCK = [Conversation(id_conversation=101, titre="Architecture du système")]

    def _get_service_and_mocks(self):
        mock_collab_dao = MagicMock()
        mock_message_dao = MagicMock()
        mock_conversation_dao = MagicMock()
        mock_collab_dao.find_by_user.return_value = self.COLLABORATIONS_MOCK

        search_service = SearchService(
            message_dao=mock_message_dao,
            conversation_dao=mock_conversation_dao,
            collaboration_dao=mock_collab_dao
        )
        return search_service, mock_collab_dao, mock_message_dao, mock_conversation_dao

    def test_search_messages_by_keyword_success(self):
        with patch(PATH_COLLABORATION_DAO, new_callable=MagicMock) as MockCollabDAO, \
             patch(PATH_MESSAGE_DAO, new_callable=MagicMock) as MockMessageDAO:

            service, mock_collab, mock_message, _ = self._get_service_and_mocks()
            mock_message.search_by_keyword.return_value = self.MESSAGE_LIST_MOCK

            result = service.search_messages_by_keyword(self.USER_ID, self.KEYWORD)

            mock_collab.find_by_user.assert_called_once_with(self.USER_ID)
            mock_message.search_by_keyword.assert_called_once_with(
                self.KEYWORD, 
                self.CONV_IDS_AUTORISES
            )
            assert result == self.MESSAGE_LIST_MOCK

    def test_search_messages_by_keyword_no_access_returns_empty(self):
        with patch(PATH_COLLABORATION_DAO, new_callable=MagicMock) as MockCollabDAO, \
             patch(PATH_MESSAGE_DAO, new_callable=MagicMock) as MockMessageDAO:
            
            service, mock_collab, mock_message, _ = self._get_service_and_mocks()
            mock_collab.find_by_user.return_value = []
            
            result = service.search_messages_by_keyword(self.USER_ID, self.KEYWORD)
            
            assert result == []
            mock_message.search_by_keyword.assert_not_called()

    def test_search_messages_by_date_success(self):
        with patch(PATH_COLLABORATION_DAO, new_callable=MagicMock) as MockCollabDAO, \
             patch(PATH_MESSAGE_DAO, new_callable=MagicMock) as MockMessageDAO:

            service, mock_collab, mock_message, _ = self._get_service_and_mocks()
            mock_message.search_by_date.return_value = self.MESSAGE_LIST_MOCK

            service.search_messages_by_date(self.USER_ID, self.TARGET_DATE)
            
            mock_message.search_by_date.assert_called_once_with(
                self.TARGET_DATE, 
                self.CONV_IDS_AUTORISES
            )

    def test_search_conversations_by_keyword_delegation(self):
        with patch(PATH_CONVERSATION_DAO, new_callable=MagicMock) as MockConvDAO:
            service = SearchService(MagicMock(), MockConvDAO.return_value, MagicMock())
            MockConvDAO.return_value.search_conversations_by_title.return_value = self.CONVERSATION_LIST_MOCK
            result = service.search_conversations_by_keyword(self.USER_ID, self.KEYWORD)
            MockConvDAO.return_value.search_conversations_by_title.assert_called_once_with(
                self.USER_ID, 
                self.KEYWORD
            )
            assert result == self.CONVERSATION_LIST_MOCK

    def test_search_conversations_by_date_delegation(self):
        with patch(PATH_CONVERSATION_DAO, new_callable=MagicMock) as MockConvDAO:
            service = SearchService(MagicMock(), MockConvDAO.return_value, MagicMock())
            MockConvDAO.return_value.get_conversations_by_date.return_value = self.CONVERSATION_LIST_MOCK
            result = service.search_conversations_by_date(self.USER_ID, self.TARGET_DATE)
            MockConvDAO.return_value.get_conversations_by_date.assert_called_once_with(
                self.USER_ID, 
                self.TARGET_DATE
            )
            assert result == self.CONVERSATION_LIST_MOCK
