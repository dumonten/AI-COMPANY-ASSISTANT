from sqlalchemy.future import select

from models import UserModel
from utils.repository import async_session


class UserRepository:
    """
    UserRepository is a class responsible for handling operations related to the UserModel.
    It provides methods for saving and updating user values in the database.
    """

    model = UserModel

    async def save_user_values(self, user_id: int, key_values: str):
        """
        Asynchronously saves user values to the database.

        Parameters:
        - user_id (int): The unique identifier for the user.
        - key_values (str): The key-value pairs to be saved for the user.

        Returns:
        - None
        """

        async with async_session() as session:
            async with session.begin():
                user_values = UserModel(user_id=user_id, key_values=key_values)
                session.add(user_values)
                await session.commit()

    async def update_user_values(self, user_id: int, key_values: str):
        """
        Asynchronously updates user values in the database.

        Parameters:
        - user_id (int): The unique identifier for the user to be updated.
        - key_values (str): The new key-value pairs to update for the user.

        Returns:
        - None

        Raises:
        - ValueError: If no user is found with the provided user_id.
        """

        async with async_session() as session:
            async with session.begin():
                user = await session.execute(
                    select(self.model).where(self.model.user_id == user_id)
                )
                user = user.scalars().first()
                if user:
                    user.key_values = key_values
                    await session.commit()
                else:
                    raise ValueError(f"No user found with user_id: {user_id}")
