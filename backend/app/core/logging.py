"""Structured logging configuration using structlog.

Call `setup_logging()` once at application startup.  Every module can then use:

    import structlog
    logger = structlog.get_logger()
"""

import logging
import sys

import structlog

from app.core.settings import Settings


def setup_logging(settings: Settings) -> None:
    """Configure structlog + stdlib logging based on application settings."""

    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    # Shared processors applied to every log entry
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.ExtraAdder(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if settings.log_json:
        # Production: machine-readable JSON lines
        renderer: structlog.types.Processor = structlog.processors.JSONRenderer()
    else:
        # Development: colourful, human-friendly output
        renderer = structlog.dev.ConsoleRenderer()

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
        foreign_pre_chain=shared_processors,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)

    if settings.loki_url:
        _add_loki_handler(root_logger, settings, shared_processors, settings.loki_url)

    # Quiet down noisy third-party loggers
    for name in ("uvicorn.access", "sqlalchemy.engine"):
        logging.getLogger(name).setLevel(logging.WARNING)


def _add_loki_handler(
    root_logger: logging.Logger,
    settings: Settings,
    shared_processors: list[structlog.types.Processor],
    loki_url: str,
) -> None:
    import queue

    import logging_loki

    loki_formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.processors.JSONRenderer(),
        ],
        foreign_pre_chain=shared_processors,
    )

    # LokiQueueHandler ships logs on a background thread so the async
    # event loop is never blocked by the HTTP push to Loki.
    loki_queue: queue.Queue = queue.Queue(-1)
    loki_handler = logging_loki.LokiQueueHandler(
        loki_queue,
        url=f"{loki_url.rstrip('/')}/loki/api/v1/push",
        tags={"app": settings.app_name, "environment": settings.environment},
        version="1",
    )
    loki_handler.setFormatter(loki_formatter)

    # Disable SSL verification on the underlying requests.Session.
    # LokiQueueHandler wraps a LokiHandler whose emitter lazily creates the
    # session; accessing .session here triggers that creation so the flag sticks.
    import urllib3

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    inner: logging_loki.LokiHandler = loki_handler.listener.handlers[0]  # type: ignore[union-attr,assignment]
    inner.emitter.session.verify = False

    root_logger.addHandler(loki_handler)
