# src/cli/context.py
from __future__ import annotations

from src.Service.UserService import UserService
from src.Service.AuthService import AuthService
from src.Service.ConversationService import ConversationService
from src.Service.MessageService import MessageService
from src.Service.SearchService import SearchService
from src.Service.CollaborationService import CollaborationService
from src.Service.FeedbackService import FeedbackService
from src.Service.LLMService import LLMService

from src.DAO.FeedbackDAO import FeedbackDAO
from src.DAO.CollaborationDAO import CollaborationDAO
from src.DAO.ConversationDAO import ConversationDAO
from src.DAO.MessageDAO import MessageDAO
from src.DAO.UserDAO import UserDAO

# DAO
user_dao = UserDAO()
message_dao = MessageDAO()
collab_dao = CollaborationDAO()
conversation_dao = ConversationDAO()
feedback_dao = FeedbackDAO()

# Services
auth_service = AuthService(user_dao)
user_service = UserService(user_dao, auth_service)

# NOTE: adapte si CollaborationService prend des DAO en paramètres
collab_service = CollaborationService()

msg_service = MessageService(
    message_dao, user_service=user_service, auth_service=auth_service
)
conv_service = ConversationService(
    conversation_dao, collab_service, user_service, msg_service
)
search_service = SearchService(message_dao, conversation_dao, collab_dao)
feedback_service = FeedbackService(feedback_dao)

llm_service = LLMService(
    message_dao=message_dao,
    conversation_dao=conversation_dao,
    user_dao=user_dao,
    # base_url / api_key : variables d'env si besoin
)
