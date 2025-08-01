#!/usr/bin/env python3
"""VFIO module - re-exports the correct implementation from vfio_handler."""

import logging
import os
from pathlib import Path
from typing import Optional

# Re-export the correct, complete VFIO implementation
from .vfio_handler import VFIOBinder, VFIOBindError, render_pretty, run_diagnostics
from .vfio_helpers import get_device_fd

# Legacy compatibility functions - these are kept for backward compatibility
# but they now use the correct implementation internally


try:
    from ..string_utils import (
        log_debug_safe,
        log_error_safe,
        log_info_safe,
        log_warning_safe,
    )
except ImportError:
    # Fallback implementations
    def log_info_safe(logger, template, **kwargs):
        logger.info(template.format(**kwargs))

    def log_error_safe(logger, template, **kwargs):
        logger.error(template.format(**kwargs))

    def log_warning_safe(logger, template, **kwargs):
        logger.warning(template.format(**kwargs))

    def log_debug_safe(logger, template, **kwargs):
        logger.debug(template.format(**kwargs))


logger = logging.getLogger(__name__)


def get_current_driver(bdf: str) -> Optional[str]:
    """Get the current driver for the device."""
    driver_link = Path(f"/sys/bus/pci/devices/{bdf}/driver")
    if driver_link.exists():
        log_info_safe(
            logger,
            "Current driver for {bdf} is {driver}",
            bdf=bdf,
            driver=driver_link.resolve().name,
            prefix="VFIO",
        )
        return driver_link.resolve().name
    return None


def restore_driver(bdf: str, original: Optional[str]):
    """Restore device to original driver."""
    if original and get_current_driver(bdf) != original:
        try:
            bind_path = Path(f"/sys/bus/pci/drivers/{original}/bind")
            if bind_path.exists():
                bind_path.write_text(f"{bdf}\n")
                log_debug_safe(
                    logger,
                    "Restored {bdf} to {driver}",
                    bdf=bdf,
                    driver=original,
                    prefix="VFIO",
                )
        except Exception as e:
            log_warning_safe(
                logger,
                "Failed to restore driver for {bdf}: {error}",
                bdf=bdf,
                error=e,
                prefix="VFIO",
            )


# Export the main symbols
__all__ = [
    "VFIOBinder",
    "VFIOBindError",
    "get_device_fd",
    "get_current_driver",
    "restore_driver",
    "run_diagnostics",
    "render_pretty",
]
