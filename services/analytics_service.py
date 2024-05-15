from analytics.amplitude_logger import AmplitudeLogger
from config import settings


class AnalyticsService:
    """
    Manages assistant operations with Amplitude analytics using a thread pool.
    """

    executor = settings.thread_executor

    tracker = AmplitudeLogger()

    @classmethod
    def track_event(cls, user_id: int, event_type: str, event_properties: str = ""):
        """
        Asynchronously tracks an event in Amplitude using the executor.

        Args:
            user_id (int): User ID.
            event_type (str): Event type.
            event_properties (str): Event properties in JSON-like string.

        Returns:
        - None
        """

        cls.executor.submit(
            cls.tracker.track_event, user_id, event_type, event_properties
        )
