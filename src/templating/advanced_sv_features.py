#!/usr/bin/env python3
"""
Advanced SystemVerilog Features Module

This module consolidates all advanced SystemVerilog generation features including
error handling, performance monitoring, and power management into a single,
cohesive module to reduce import complexity.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set

# Import standard utilities
try:
    from ..string_utils import (
        generate_sv_header_comment,
        log_debug_safe,
        log_error_safe,
        log_info_safe,
        log_warning_safe,
        safe_format,
    )
    from .template_renderer import TemplateRenderer, TemplateRenderError
except ImportError:
    # Fallback for standalone usage
    from src.string_utils import (
        generate_sv_header_comment,
        log_debug_safe,
        log_error_safe,
        log_info_safe,
        log_warning_safe,
        safe_format,
    )
    from src.templating.template_renderer import TemplateRenderer, TemplateRenderError

# Setup logger
logger = logging.getLogger(__name__)


class PowerState(Enum):
    """PCIe power states."""

    D0 = "D0"  # Fully operational
    D1 = "D1"  # Light sleep
    D2 = "D2"  # Deep sleep
    D3_HOT = "D3_HOT"  # Deep sleep with aux power
    D3_COLD = "D3_COLD"  # No power


class ErrorType(Enum):
    """Types of errors that can be detected and handled."""

    NONE = "none"
    PARITY = "parity"
    CRC = "crc"
    TIMEOUT = "timeout"
    OVERFLOW = "overflow"
    UNDERFLOW = "underflow"
    PROTOCOL = "protocol"
    ALIGNMENT = "alignment"
    INVALID_TLP = "invalid_tlp"
    UNSUPPORTED = "unsupported"


class PerformanceMetric(Enum):
    """Performance metrics that can be monitored."""

    TLP_COUNT = "tlp_count"
    COMPLETION_LATENCY = "completion_latency"
    BANDWIDTH_UTILIZATION = "bandwidth_utilization"
    ERROR_RATE = "error_rate"
    POWER_TRANSITIONS = "power_transitions"
    INTERRUPT_LATENCY = "interrupt_latency"


@dataclass
class ErrorHandlingConfig:
    """Configuration for error handling features."""

    enable_error_detection: bool = True
    enable_error_injection: bool = False
    enable_error_logging: bool = True
    error_log_depth: int = 256
    recoverable_errors: Set[ErrorType] = field(
        default_factory=lambda: {ErrorType.PARITY, ErrorType.CRC, ErrorType.TIMEOUT}
    )
    fatal_errors: Set[ErrorType] = field(
        default_factory=lambda: {ErrorType.PROTOCOL, ErrorType.INVALID_TLP}
    )
    error_thresholds: Dict[ErrorType, int] = field(
        default_factory=lambda: {
            ErrorType.PARITY: 10,
            ErrorType.CRC: 5,
            ErrorType.TIMEOUT: 3,
        }
    )


@dataclass
class PerformanceConfig:
    """Configuration for performance monitoring."""

    enable_performance_counters: bool = True
    counter_width: int = 32
    sampling_period: int = 1000  # Clock cycles
    metrics_to_monitor: Set[PerformanceMetric] = field(
        default_factory=lambda: {
            PerformanceMetric.TLP_COUNT,
            PerformanceMetric.COMPLETION_LATENCY,
            PerformanceMetric.BANDWIDTH_UTILIZATION,
        }
    )
    enable_histograms: bool = False
    histogram_bins: int = 16


@dataclass
class PowerManagementConfig:
    """Configuration for power management features."""

    enable_power_management: bool = True
    supported_states: Set[PowerState] = field(
        default_factory=lambda: {PowerState.D0, PowerState.D3_HOT}
    )
    transition_delays: Dict[tuple, int] = field(
        default_factory=lambda: {
            (PowerState.D0, PowerState.D3_HOT): 100,
            (PowerState.D3_HOT, PowerState.D0): 1000,
        }
    )
    enable_clock_gating: bool = True
    enable_power_gating: bool = False
    idle_threshold: int = 10000  # Clock cycles before entering low power


@dataclass
class AdvancedFeatureConfig:
    """Combined configuration for all advanced features."""

    error_handling: ErrorHandlingConfig = field(default_factory=ErrorHandlingConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    power_management: PowerManagementConfig = field(
        default_factory=PowerManagementConfig
    )

    # Global settings
    enable_debug_ports: bool = True
    enable_assertions: bool = True
    enable_coverage: bool = False
    clock_frequency_mhz: int = 250


class AdvancedSVFeatureGenerator:
    """Generator for advanced SystemVerilog features."""

    def __init__(self, config: AdvancedFeatureConfig):
        self.config = config
        self.renderer = TemplateRenderer()
        log_info_safe(
            logger,
            "Initialized AdvancedSVFeatureGenerator with config",
            prefix="GENERATOR",
        )

    def generate_error_handling_module(self) -> str:
        """Generate complete error handling module."""
        if not self.config.error_handling.enable_error_detection:
            log_debug_safe(
                logger,
                "Error handling disabled, returning empty module",
                prefix="ERROR_GEN",
            )
            return ""

        log_info_safe(logger, "Generating error handling module", prefix="ERROR_GEN")

        try:
            # Import here to avoid circular imports
            from .advanced_sv_error import ErrorHandlingConfig, ErrorHandlingGenerator

            # Create error handling configuration from our config
            error_config = ErrorHandlingConfig(
                enable_ecc=self.config.error_handling.enable_error_detection,
                enable_parity_check=self.config.error_handling.enable_error_detection,
                enable_crc_check=self.config.error_handling.enable_error_detection,
                enable_timeout_detection=self.config.error_handling.enable_error_detection,
                enable_auto_retry=True,
                max_retry_count=3,
                enable_error_logging=self.config.error_handling.enable_error_logging,
                enable_error_injection=self.config.error_handling.enable_error_injection,
            )

            # Create error handling generator
            error_generator = ErrorHandlingGenerator(error_config)

            # Generate error handling components using templates
            context = {"config": self.config.error_handling}

            error_detection = error_generator.generate_error_detection()
            error_state_machine = error_generator.generate_error_state_machine()
            error_logging = error_generator.generate_error_logging()
            error_counters = error_generator.generate_error_counters()

            # Add error injection if enabled
            error_injection = ""
            if self.config.error_handling.enable_error_injection:
                error_injection = error_generator.generate_error_injection()
                log_debug_safe(
                    logger, "Added error injection logic", prefix="ERROR_GEN"
                )

            # Generate the complete module using template
            return self._generate_module_template(
                "error_handler",
                context,
                error_detection,
                error_state_machine,
                error_logging,
                error_counters,
                error_injection,
            )

        except ImportError as e:
            log_error_safe(
                logger,
                "Failed to import error handling generator: {error}",
                prefix="ERROR_GEN",
                error=str(e),
            )
            return self._generate_fallback_error_module()
        except Exception as e:
            log_error_safe(
                logger,
                "Error generating error handling module: {error}",
                prefix="ERROR_GEN",
                error=str(e),
            )
            return self._generate_fallback_error_module()

    def generate_performance_monitor_module(self) -> str:
        """Generate performance monitoring module."""
        if not self.config.performance.enable_performance_counters:
            log_debug_safe(
                logger,
                "Performance monitoring disabled, returning empty module",
                prefix="PERF_GEN",
            )
            return ""

        log_info_safe(
            logger, "Generating performance monitoring module", prefix="PERF_GEN"
        )

        try:
            context = {
                "config": self.config.performance,
                "counter_width": self.config.performance.counter_width,
                "sampling_period": self.config.performance.sampling_period,
                "metrics": list(self.config.performance.metrics_to_monitor),
            }

            return self._generate_module_template(
                "performance_monitor",
                context,
                self._generate_counter_logic(),
                self._generate_sampling_logic(),
                self._generate_reporting_logic(),
            )
        except Exception as e:
            log_error_safe(
                logger,
                "Error generating performance monitor module: {error}",
                prefix="PERF_GEN",
                error=str(e),
            )
            return self._generate_fallback_performance_module()

    def generate_power_management_module(self) -> str:
        """Generate power management module."""
        if not self.config.power_management.enable_power_management:
            log_debug_safe(
                logger,
                "Power management disabled, returning empty module",
                prefix="POWER_GEN",
            )
            return ""

        log_info_safe(logger, "Generating power management module", prefix="POWER_GEN")

        try:
            context = {
                "config": self.config.power_management,
                "supported_states": list(self.config.power_management.supported_states),
                "enable_clock_gating": self.config.power_management.enable_clock_gating,
                "enable_power_gating": self.config.power_management.enable_power_gating,
            }

            return self._generate_module_template(
                "power_manager",
                context,
                self._generate_state_machine(),
                self._generate_clock_gating_logic(),
                self._generate_transition_logic(),
            )
        except Exception as e:
            log_error_safe(
                logger,
                "Error generating power management module: {error}",
                prefix="POWER_GEN",
                error=str(e),
            )
            return self._generate_fallback_power_module()

    def _generate_fallback_error_module(self) -> str:
        """Generate a fallback error handling module when template generation fails."""
        log_warning_safe(
            logger, "Using fallback error handling module", prefix="FALLBACK"
        )

        context = {"config": self.config.error_handling}
        return self._generate_fallback_module(
            "error_handler",
            context,
            self._generate_error_recovery_logic(),
            self._generate_error_logging_logic(),
        )

    def _generate_fallback_performance_module(self) -> str:
        """Generate a fallback performance monitoring module when template generation fails."""
        log_warning_safe(
            logger, "Using fallback performance monitoring module", prefix="FALLBACK"
        )

        context = {"config": self.config.performance}
        return self._generate_fallback_module(
            "performance_monitor",
            context,
            self._generate_counter_logic(),
            self._generate_sampling_logic(),
            self._generate_reporting_logic(),
        )

    def _generate_fallback_power_module(self) -> str:
        """Generate a fallback power management module when template generation fails."""
        log_warning_safe(
            logger, "Using fallback power management module", prefix="FALLBACK"
        )

        context = {"config": self.config.power_management}
        return self._generate_fallback_module(
            "power_manager",
            context,
            self._generate_state_machine(),
            self._generate_clock_gating_logic(),
            self._generate_transition_logic(),
        )

    def _generate_module_template(
        self, module_name: str, context: Dict, *components: str
    ) -> str:
        """Generate a module template with the given components using Jinja2 templates."""
        try:
            log_debug_safe(
                logger,
                "Generating module template for {module}",
                prefix="TEMPLATE",
                module=module_name,
            )

            # Try to use Jinja2 template first
            template_name = safe_format(
                "sv/advanced/{module_name}.sv.j2", module_name=module_name
            )

            try:
                return self.renderer.render_template(template_name, context)
            except TemplateRenderError:
                log_warning_safe(
                    logger,
                    "Template {template_name} not found, using fallback generation",
                    prefix="TEMPLATE",
                    template_name=template_name,
                )
                return self._generate_fallback_module(module_name, context, *components)

        except Exception as e:
            log_error_safe(
                logger,
                "Error in template generation: {error}",
                prefix="TEMPLATE",
                error=str(e),
            )
            return self._generate_fallback_module(module_name, context, *components)

    def _generate_fallback_module(
        self, module_name: str, context: Dict, *components: str
    ) -> str:
        """Generate a fallback module when templates are not available."""
        log_info_safe(
            logger,
            "Using fallback module generation for {module}",
            prefix="FALLBACK",
            module=module_name,
        )

        header = generate_sv_header_comment(
            safe_format(
                "{module_name} Module",
                module_name=module_name.replace("_", " ").title(),
            ),
            generator="AdvancedSVFeatureGenerator",
            version="0.7.5",
        )

        module_body = "\n\n".join(filter(None, components))

        # Generate appropriate ports based on module type
        port_definitions = self._generate_module_ports(module_name)

        return safe_format(
            """{header}

module {module_name} #(
    parameter FEATURE_ENABLED = 1
) (
    // Clock and Reset
    input  logic        clk,
    input  logic        rst_n,
{port_definitions}
);

{module_body}

endmodule
""",
            header=header,
            module_name=module_name,
            port_definitions=port_definitions,
            module_body=module_body,
        )

    def _generate_module_ports(self, module_name: str) -> str:
        """Generate appropriate ports based on module type."""
        log_debug_safe(
            logger,
            "Generating ports for {module_name}",
            prefix="PORTS",
            module_name=module_name,
        )

        if module_name == "error_handler":
            return """
    // Error signals
    input  logic        error_detected,
    input  logic [7:0]  error_type,
    output logic        recovery_active"""
        elif module_name == "performance_monitor":
            return """
    // Performance monitoring signals
    input  logic        transaction_valid,
    input  logic [31:0] performance_data,
    input  logic        sample_trigger,
    input  logic [31:0] threshold,
    output logic        report_ready,
    output logic [31:0] report_data"""
        elif module_name == "power_manager":
            return """
    // Power management signals
    input  logic        power_down_req,
    input  logic        power_up_req,
    input  logic        power_off_req,
    input  logic        power_save_mode,
    output logic        gated_clk,
    output logic        transition_complete"""
        else:
            log_warning_safe(
                logger,
                "Unknown module type {module_name}, using default ports",
                prefix="PORTS",
                module_name=module_name,
            )
            return ""

    def _generate_error_recovery_logic(self) -> str:
        """Generate error recovery logic."""
        log_debug_safe(logger, "Generating error recovery logic", prefix="ERROR_LOGIC")

        context = {
            "config": self.config.error_handling,
            "recoverable_errors": list(self.config.error_handling.recoverable_errors),
            "fatal_errors": list(self.config.error_handling.fatal_errors),
            "error_thresholds": self.config.error_handling.error_thresholds,
        }
        return self.renderer.render_template("sv/error_recovery.sv.j2", context)

    def _generate_error_logging_logic(self) -> str:
        """Generate error logging logic."""
        log_debug_safe(logger, "Generating error logging logic", prefix="ERROR_LOGIC")

        context = {"config": self.config.error_handling}
        return self.renderer.render_template("sv/error_logging.sv.j2", context)

    def _generate_counter_logic(self) -> str:
        """Generate performance counter logic."""
        log_debug_safe(
            logger, "Generating performance counter logic", prefix="PERF_LOGIC"
        )

        context = {"config": self.config.performance}
        return self.renderer.render_template("sv/performance_counters.sv.j2", context)

    def _generate_sampling_logic(self) -> str:
        """Generate sampling logic."""
        log_debug_safe(logger, "Generating sampling logic", prefix="PERF_LOGIC")

        context = {"config": self.config.performance}
        return self.renderer.render_template("sv/sampling_logic.sv.j2", context)

    def _generate_reporting_logic(self) -> str:
        """Generate reporting logic."""
        log_debug_safe(logger, "Generating reporting logic", prefix="PERF_LOGIC")

        context = {"config": self.config.performance}
        return self.renderer.render_template("sv/reporting_logic.sv.j2", context)

    def _generate_state_machine(self) -> str:
        """Generate power state machine."""
        log_debug_safe(logger, "Generating power state machine", prefix="POWER_LOGIC")

        context = {"config": self.config.power_management}
        return self.renderer.render_template("sv/power_management.sv.j2", context)

    def _generate_clock_gating_logic(self) -> str:
        """Generate clock gating logic."""
        log_debug_safe(logger, "Generating clock gating logic", prefix="POWER_LOGIC")

        if not self.config.power_management.enable_clock_gating:
            log_debug_safe(
                logger, "Clock gating disabled, skipping", prefix="POWER_LOGIC"
            )
            return ""

        context = {"config": self.config.power_management}
        return self.renderer.render_template("sv/clock_gating.sv.j2", context)

    def _generate_transition_logic(self) -> str:
        """Generate power transition logic."""
        log_debug_safe(
            logger, "Generating power transition logic", prefix="POWER_LOGIC"
        )

        context = {"config": self.config.power_management}
        return self.renderer.render_template("sv/power_transitions.sv.j2", context)


# Export the main components
__all__ = [
    "PowerState",
    "ErrorType",
    "PerformanceMetric",
    "ErrorHandlingConfig",
    "PerformanceConfig",
    "PowerManagementConfig",
    "AdvancedFeatureConfig",
    "AdvancedSVFeatureGenerator",
]
