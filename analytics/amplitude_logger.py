from amplitude import Amplitude, BaseEvent
from loguru import logger

from config import settings


class AmplitudeLogger:
    """
    Logger with a client for Amplitude API.
    """

    def __init__(self):
        """
        Initializes AmplitudeLogger client with Amplitude API key.
        """

        self.client = Amplitude(settings.AMPLITUDE_KEY)

    def track_event(self, user_id: int, event_type: str, event_properties: str):
        """
        Tracks an event in Amplitude with user ID, event type, and properties.

        Parameters:
            user_id (int): User ID.
            event_type (str): Event type.
            event_properties (str): Event properties in JSON-like string.

        Returns:
        - None
        """

        try:
            user_id = str(user_id)
            self.client.track(
                BaseEvent(
                    user_id=user_id,
                    event_type=event_type,
                    event_properties={"info": event_properties},
                )
            )
        except Exception as e:
            logger.info(f"Error in amplitude logger: {e}")
