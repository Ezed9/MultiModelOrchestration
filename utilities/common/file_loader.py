"""
File loader utilities.
"""

import logging
import os

logger = logging.getLogger(__name__)


def load_instructions_file(filename: str, default: str = "") -> str:
    """
    Load instructions from a file.
    
    Args:
        filename: Path to the instructions file
        default: Default value if file cannot be loaded
        
    Returns:
        The content of the instructions file or the default value
        
    Note:
        Returns default (not raises) on error to allow graceful degradation.
    """
    if not filename:
        return default

    try:
        if os.path.exists(filename):
            with open(filename, encoding="utf-8") as file:
                content = file.read()
                logger.debug(f"Loaded instructions from: {filename}")
                return content
        else:
            logger.warning(f"Instructions file not found: {filename}")
    except OSError as e:
        logger.error(f"Failed to read instructions file {filename}: {e}")
    except UnicodeDecodeError as e:
        logger.error(f"Encoding error in {filename}: {e}")

    return default