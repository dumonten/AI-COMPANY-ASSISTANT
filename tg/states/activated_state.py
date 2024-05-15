from aiogram.fsm.state import State, StatesGroup


class ActivatedState(StatesGroup):
    """
    Defines the 'thread_id' state within the FSM. This state is used to manage or
    process information related to a specific thread ID.
    """

    wait_url = State()
    activated = State()
