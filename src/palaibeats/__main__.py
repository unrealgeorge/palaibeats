"""Entry point: `python -m palaibeats`."""

from __future__ import annotations

import logging

from dotenv import load_dotenv

from palaibeats.bot import PalaiBeatsBot
from palaibeats.config import load_settings
from palaibeats.logging_config import configure_logging

logger = logging.getLogger(__name__)


def main() -> None:
    load_dotenv()
    settings = load_settings()
    configure_logging(settings.log_level)

    logger.info("Starting PalaiBeats for guild %s", settings.guild_id)
    bot = PalaiBeatsBot(settings)
    try:
        bot.run(settings.discord_token, log_handler=None)
    except KeyboardInterrupt:
        logger.info("Interrupted, shutting down.")


if __name__ == "__main__":
    main()
