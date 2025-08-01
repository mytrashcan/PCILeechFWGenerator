#!/usr/bin/env python3
"""
Simplified SystemVerilog Power Management Module

This module provides minimal power management logic generation for PCIe devices,
focusing on essential D-state transitions and PME support using a simplified approach
based on the pmcsr_stub.sv module design.

Simplified Power Management feature for the PCILeechFWGenerator project.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from ..string_utils import generate_sv_header_comment
from .template_renderer import TemplateRenderer


class PowerState(Enum):
    """PCIe power states as defined in the PCIe specification."""

    D0 = "D0"  # Fully operational
    D1 = "D1"  # Low power state 1
    D2 = "D2"  # Low power state 2
    D3_HOT = "D3hot"  # Hot reset state
    D3_COLD = "D3cold"  # Cold reset state


@dataclass
class TransitionCycles:
    """Power state transition cycle counts."""

    d0_to_d1: int = 100
    d1_to_d0: int = 50
    d0_to_d3: int = 200
    d3_to_d0: int = 150


@dataclass
class PowerManagementConfig:
    """Configuration for power management features."""

    # Clock frequency for timing calculations
    clk_hz: int = 100_000_000  # 100 MHz default

    # Transition timeout (nanoseconds) - PCIe spec allows up to 10ms
    transition_timeout_ns: int = 10_000_000  # 10 ms

    # Enable PME (Power Management Event) support
    enable_pme: bool = True

    # Enable wake event support
    enable_wake_events: bool = False

    # Transition cycle counts
    transition_cycles: Optional[TransitionCycles] = None

    def __post_init__(self):
        if self.transition_cycles is None:
            self.transition_cycles = TransitionCycles()


class PowerManagementGenerator:
    """Generator for simplified power management SystemVerilog logic."""

    def __init__(self, config: Optional[PowerManagementConfig] = None):
        """Initialize the power management generator."""
        self.config = config or PowerManagementConfig()
        self.renderer = TemplateRenderer()

    def _get_template_context(self) -> dict:
        """Get template context variables from configuration."""
        return {
            "clk_hz": self.config.clk_hz,
            "tr_ns": self.config.transition_timeout_ns,
            "timeout_ms": self.config.transition_timeout_ns // 1_000_000,
            "enable_pme": self.config.enable_pme,
            "enable_wake_events": self.config.enable_wake_events,
        }

    def generate_pmcsr_stub_module(self) -> str:
        """Generate the complete pmcsr_stub module based on the provided design."""
        context = self._get_template_context()
        return self.renderer.render_template(
            "systemverilog/modules/pmcsr_stub.sv.j2", context
        )

    def generate_power_management_integration(self) -> str:
        """Generate integration code for the power management module."""
        context = self._get_template_context()
        return self.renderer.render_template(
            "systemverilog/components/power_integration.sv.j2", context
        )

    def generate_power_declarations(self) -> str:
        """Generate minimal power management signal declarations."""
        context = self._get_template_context()
        return self.renderer.render_template(
            "systemverilog/components/power_declarations.sv.j2", context
        )

    def generate_complete_power_management(self) -> str:
        """Generate complete simplified power management logic."""

        header = generate_sv_header_comment(
            "Simplified Power Management Module",
            description="Based on minimal pmcsr_stub design for essential PCIe power management",
        )

        # Generate the individual components using templates
        declarations = self.generate_power_declarations()
        integration = self.generate_power_management_integration()

        # Build monitoring and status outputs based on configuration
        monitoring_lines = [
            "    // ── Power State Monitoring ──────────────────────────────────────────",
            "    assign current_power_state = pmcsr_rdata[1:0];",
            "    assign power_management_enabled = 1'b1;",
        ]

        if self.config.enable_pme:
            monitoring_lines.extend(
                [
                    "    assign pme_enable = pmcsr_rdata[15];",
                    "    assign pme_status = pmcsr_rdata[14];",
                ]
            )

        status_lines = [
            "",
            "    // ── Power Management Status Outputs ─────────────────────────────────",
            "    // These can be used by other modules to check power state",
            "    assign power_state_d0 = (current_power_state == 2'b00);",
            "    assign power_state_d3 = (current_power_state == 2'b11);",
        ]

        if self.config.enable_pme:
            status_lines.append("    assign power_event_pending = pme_status;")

        components = (
            [
                header,
                "",
                declarations,
                "",
                integration,
                "",
            ]
            + monitoring_lines
            + status_lines
            + [""]
        )

        return "\n".join(components)

    def get_module_dependencies(self) -> list:
        """Return list of module dependencies."""
        return ["pmcsr_stub"]

    def get_config_space_requirements(self) -> dict:
        """Return config space requirements for power management."""
        return {
            "pmcsr_offset": "0x44",
            "pmcsr_size": "16 bits",
            "description": "Power Management Control/Status Register",
        }
