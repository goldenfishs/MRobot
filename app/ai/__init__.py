"""Shared AI assistant core for MRobot frontends."""

from .client import AIClientError, AICancelled, OpenAICompatibleClient
from .config import AIConversationStore, AIProfileStore
from .models import AIProviderConfig, AssistantResult, Conversation, PROVIDER_PRESETS
from .service import MRobotAssistant
from .tools import MRobotToolRegistry

__all__ = [
    "AIClientError",
    "AICancelled",
    "AIConversationStore",
    "AIProfileStore",
    "AIProviderConfig",
    "AssistantResult",
    "Conversation",
    "MRobotAssistant",
    "MRobotToolRegistry",
    "OpenAICompatibleClient",
    "PROVIDER_PRESETS",
]
