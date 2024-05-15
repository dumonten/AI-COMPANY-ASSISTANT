import base64


def encode_image(image_path: str) -> str:
    """
    Encodes an image file into a base64 string.

    This function reads an image file from the given path, encodes it into a base64 string,
    and returns the encoded string.

    Parameters:
    - image_path (str): The file path of the image to be encoded.

    Returns:
    - str: A base64 encoded string representing the image.
    """

    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")
