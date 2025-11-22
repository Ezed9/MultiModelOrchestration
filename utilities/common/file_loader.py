import os

def load_instructions_file(filename: str, default: str = "") -> str:
    """
    Load instructions from a file. If the file does not exist,
    return the default instructions.

    Args:
        filename (str): Path to the instructions file
        default (str): Default instructions if file is not found

    Returns:
        str: The content of the instructions file or the default value
    """
    if not filename:
        return default

    try:
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as file:
                return file.read()
    except Exception as e:
        print(f"Error loading instructions file: {e}")

    return default