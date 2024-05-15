class Emotions:
    """
    A class to define a fixed set of emotions that can be identified in images.
    This class is intended to be used by services like EmotionService to specify the possible emotional states that can be detected.
    """

    POSSIBLE_EMOTIONS = [
        "anger",
        "disgust",
        "fear",
        "happiness",
        "sadness",
        "surprise",
        "calm",
    ]
