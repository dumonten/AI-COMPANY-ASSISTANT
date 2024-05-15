from sqlalchemy import Column, Integer, String

from utils.repository import Base


class UserModel(Base):
    """
    Represents the structure of the 'user' table in the database.
    It inherits from the Base class, which is a declarative base for SQLAlchemy models.
    This class defines the columns and their types that will be used to create the 'user' table.
    """

    __tablename__ = "user"

    # 'id' is an integer column that serves as the primary key for the 'user' table.
    # Primary keys are unique identifiers for each record in the table.
    id = Column(Integer, primary_key=True)

    # 'user_id' is an integer column that must be unique across all records in the 'user' table.
    # This means that no two users can have the same user_id.
    user_id = Column(Integer, unique=True)

    # 'key_values' is a string column that can store any string data.
    # This column is used to store key-value pairs or any other string data associated with a user.
    key_values = Column(String)
