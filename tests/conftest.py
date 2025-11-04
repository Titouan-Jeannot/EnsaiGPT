import pytest

import pytest

from src.DAO.CollaborationDAO import CollaborationDAO
from src.DAO.ConversationDAO import ConversationDAO
from src.DAO.FeedbackDAO import FeedbackDAO
from src.DAO.Message_DAO import MessageDAO
from src.DAO.User_DAO import UserDAO
from src.Service.AuthService import AuthService
from src.Service.CollaborationService import CollaborationService
from src.Service.ConversationService import ConversationService
from src.Service.ExportService import ExportService
from src.Service.FeedbackService import FeedbackService
from src.Service.LLMService import LLMService
from src.Service.MessageService import MessageService
from src.Service.MotsBannisService import MotsBannisService
from src.Service.SearchService import SearchService
from src.Service.StatisticsService import StatisticsService
from src.Service.UserService import UserService


@pytest.fixture
def user_dao():
    return UserDAO()


@pytest.fixture
def conversation_dao():
    return ConversationDAO()


@pytest.fixture
def collaboration_dao():
    return CollaborationDAO()


@pytest.fixture
def message_dao():
    return MessageDAO()


@pytest.fixture
def feedback_dao():
    return FeedbackDAO()


@pytest.fixture
def auth_service(user_dao):
    return AuthService(user_dao=user_dao)


@pytest.fixture
def user_service(user_dao, auth_service):
    return UserService(user_dao=user_dao, auth_service=auth_service)


@pytest.fixture
def conversation_service(conversation_dao, collaboration_dao):
    return ConversationService(
        conversation_dao=conversation_dao,
        collaboration_dao=collaboration_dao,
    )


@pytest.fixture
def collaboration_service(collaboration_dao, user_dao, conversation_dao):
    return CollaborationService(
        collaboration_dao=collaboration_dao,
        user_dao=user_dao,
        conversation_dao=conversation_dao,
    )


@pytest.fixture
def message_service(message_dao, conversation_dao, collaboration_dao):
    return MessageService(
        message_dao=message_dao,
        conversation_dao=conversation_dao,
        collaboration_dao=collaboration_dao,
    )


@pytest.fixture
def feedback_service(feedback_dao, message_dao):
    return FeedbackService(feedback_dao=feedback_dao, message_dao=message_dao)


@pytest.fixture
def search_service(message_dao, conversation_dao, collaboration_dao):
    return SearchService(
        message_dao=message_dao,
        conversation_dao=conversation_dao,
        collaboration_dao=collaboration_dao,
    )


@pytest.fixture
def export_service(conversation_dao, message_dao):
    return ExportService(conversation_dao=conversation_dao, message_dao=message_dao)


@pytest.fixture
def statistics_service(user_dao, conversation_dao, message_dao, collaboration_dao):
    return StatisticsService(
        user_dao=user_dao,
        conversation_dao=conversation_dao,
        message_dao=message_dao,
        collaboration_dao=collaboration_dao,
    )


@pytest.fixture
def llm_service(conversation_dao, message_dao):
    return LLMService(conversation_dao=conversation_dao, message_dao=message_dao)


@pytest.fixture
def mots_bannis_service():
    return MotsBannisService()
