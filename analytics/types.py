from enum import Enum


class EventType(Enum):
    """
    EventType represents different types of events for analytical business logic.
    """

    ImageSent = "Image Sent"
    TextMessageSent = "Text Message Sent"
    VoiceMessageSent = "Voice Message Sent"
    KeyValueRevealed = "Key Value Revealed"
    ClearCommand = "Clear Command"
    GetSourcesCommand = "Get Sources Command"
    StartCommand = "Start Command"
    HelpCommand = "Help Command"
