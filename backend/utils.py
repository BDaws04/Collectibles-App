def valid_image(filename: str) -> bool:
    """
    Check if the file is a valid image based on its extension.
    """
    valid_extensions = {'.jpg', '.jpeg', '.png'}
    return any(filename.lower().endswith(ext) for ext in valid_extensions)