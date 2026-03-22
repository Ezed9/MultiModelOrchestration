"""
Website Builder Simple Agent.

A simple agent that generates HTML, CSS, and JavaScript for web pages.
"""

import logging
from utilities.common.base_agent import BaseAgent

from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)


class WebsiteBuilderSimple(BaseAgent):
    """
    A simple website builder agent that can create basic
    web pages using Google's development framework.
    """

    def __init__(self):
        super().__init__(
            name="website_builder_simple",
            instructions_file="agents/website_builder_simple/instructions.txt",
            description_file="agents/website_builder_simple/description.txt",
            lazy_init=False,
        )
        logger.info("WebsiteBuilderSimple agent initialized")
