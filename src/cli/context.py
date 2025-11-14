# src/cli/context.py
from __future__ import annotations

from Service.UserService import UserService
from Service.AuthService import AuthService
from Service.ConversationService import ConversationService
from Service.MessageService import MessageService
from Service.SearchService import SearchService
from Service.CollaborationService import CollaborationService
from Service.FeedbackService import FeedbackService
from Service.LLMService import LLMService

from DAO.FeedbackDAO import FeedbackDAO
from DAO.CollaborationDAO import CollaborationDAO
from DAO.ConversationDAO import ConversationDAO
from DAO.MessageDAO import MessageDAO
from DAO.UserDAO import UserDAO

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
