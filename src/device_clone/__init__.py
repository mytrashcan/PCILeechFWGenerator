#!/usr/bin/env python3
"""
Device Clone Module

This module contains all the device cloning related functionality including:
- Board configuration and capability management
- PCI configuration space management
- MSI-X capability handling
- Device configuration and identification
- Manufacturing variance simulation
- Behavior profiling
- PCI capability processing and manipulation

The module is organized to provide a clean separation of device cloning
functionality from the rest of the PCILeech firmware generation system.
"""

# PCI capability processing
from ..pci_capability import *
from .behavior_profiler import (
    BehaviorProfile,
    BehaviorProfiler,
    RegisterAccess,
    TimingPattern,
)

# Core device cloning functionality
from .board_config import (
    get_board_info,
    get_fpga_family,
    get_fpga_part,
    get_pcie_ip_type,
    get_pcileech_board_config,
    list_supported_boards,
    validate_board,
)
from .config_space_manager import ConfigSpaceManager
from .constants import *
from .device_config import (
    DeviceCapabilities,
    DeviceClass,
    DeviceConfigManager,
    DeviceConfiguration,
    DeviceIdentification,
    DeviceType,
    PCIeRegisters,
    get_config_manager,
    get_device_config,
    validate_hex_id,
)

# Manufacturing variance and behavior profiling
from .manufacturing_variance import DeviceClass as VarianceDeviceClass
from .manufacturing_variance import (
    ManufacturingVarianceSimulator,
    VarianceModel,
    VarianceParameters,
    VarianceType,
)
from .msix_capability import (
    find_cap,
    generate_msix_capability_registers,
    generate_msix_table_sv,
    hex_to_bytes,
    is_valid_offset,
    msix_size,
    parse_msix_capability,
    read_u16_le,
    read_u32_le,
    validate_msix_configuration,
)

# PCILeech generator
from .pcileech_generator import PCILeechGenerationConfig, PCILeechGenerator
from .variance_manager import VarianceManager

__all__ = [
    # Board configuration
    "get_fpga_part",
    "get_fpga_family",
    "get_pcie_ip_type",
    "get_pcileech_board_config",
    "get_board_info",
    "validate_board",
    "list_supported_boards",
    # Device configuration
    "DeviceType",
    "DeviceClass",
    "PCIeRegisters",
    "DeviceIdentification",
    "DeviceCapabilities",
    "DeviceConfiguration",
    "DeviceConfigManager",
    "get_config_manager",
    "get_device_config",
    "validate_hex_id",
    # Config space management
    "ConfigSpaceManager",
    # MSI-X capability
    "hex_to_bytes",
    "read_u16_le",
    "read_u32_le",
    "is_valid_offset",
    "find_cap",
    "msix_size",
    "parse_msix_capability",
    "generate_msix_table_sv",
    "validate_msix_configuration",
    "generate_msix_capability_registers",
    # Manufacturing variance
    "VarianceDeviceClass",
    "VarianceType",
    "VarianceParameters",
    "VarianceModel",
    "ManufacturingVarianceSimulator",
    # Behavior profiling
    "RegisterAccess",
    "TimingPattern",
    "BehaviorProfile",
    "BehaviorProfiler",
    "VarianceManager",
    # PCILeech generator
    "PCILeechGenerator",
    "PCILeechGenerationConfig",
]
