"""
Content Writer Agent.

A text-only specialist that writes marketing copy, taglines,
summaries, and blog outlines.
"""

import logging

from dotenv import load_dotenv

from utilities.common.base_agent import BaseAgent

load_dotenv()

logger = logging.getLogger(__name__)


class ContentWriter(BaseAgent):
    """A specialist agent for writing and summarizing text content."""

    def __init__(self):
        super().__init__(
            name="content_writer",
            instructions_file="agents/content_writer/instructions.txt",
            description_file="agents/content_writer/description.txt",
            lazy_init=False,
        )
        logger.info("ContentWriter agent initialized")
