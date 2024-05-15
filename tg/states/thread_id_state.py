from aiogram.fsm.state import State, StatesGroup


class ThreadIdState(StatesGroup):
    """
    Defines the 'thread_id' state within the FSM. This state is used to manage or
    process information related to a specific thread ID.
    """

    # thread_id (State): A state object representing the 'thread_id' state.
    thread_id = State()
