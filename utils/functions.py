import uuid


def generate_uuid():
    my_uuid = uuid.uuid4()
    uuid_str = str(my_uuid)
    return uuid_str
