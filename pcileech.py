#!/usr/bin/env python3
"""
PCILeech Firmware Generator - Unified Entry Point with Requirements Enforcement

This is the single entry point for all PCILeech functionality with automatic
dependency checking and installation.
"""

import argparse
import importlib
import logging
import os
import subprocess
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))


class RequirementsError(Exception):
    """Raised when requirements cannot be satisfied."""

    pass


def check_and_install_requirements():
    """Check if all requirements are installed and optionally install them."""
    requirements_file = project_root / "requirements.txt"

    if not requirements_file.exists():
        print("⚠️  Warning: requirements.txt not found")
        return True

    # Parse requirements.txt
    missing_packages = []
    with open(requirements_file, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Handle different requirement formats
            package_name = (
                line.split("==")[0]
                .split(">=")[0]
                .split("<=")[0]
                .split("~=")[0]
                .split("!=")[0]
            )
            package_name = package_name.strip()

            # Skip git+https and other URL-based requirements for now
            if package_name.startswith(("git+", "http://", "https://", "-e")):
                continue

            # Check if package is importable
            if not is_package_available(package_name):
                missing_packages.append(line.strip())

    if not missing_packages:
        return True

    print("❌ Missing required packages:")
    for pkg in missing_packages:
        print(f"   - {pkg}")

    # Ask user if they want to install
    if os.getenv("PCILEECH_AUTO_INSTALL") == "1":
        install = True
    else:
        print("\nOptions:")
        print("1. Auto-install missing packages (requires pip)")
        print("2. Exit and install manually")
        print("3. Continue anyway (may cause errors)")

        if not os.isatty(sys.stdin.fileno()):
            print(
                "\nError: Non-interactive environment detected. Unable to prompt for input."
            )
            print(
                "Set PCILEECH_AUTO_INSTALL=1 to auto-install or run the script in an interactive terminal."
            )
            sys.exit(1)

        choice = input("\nChoice [1/2/3]: ").strip()
        install = choice == "1"

        if choice == "2":
            print("\nTo install manually:")
            print(f"pip install -r {requirements_file}")
            print("\nOr set PCILEECH_AUTO_INSTALL=1 to auto-install next time")
            sys.exit(1)
        elif choice == "3":
            print("⚠️  Continuing without installing dependencies...")
            return False

    if install:
        return install_requirements(requirements_file)

    return False


def is_package_available(package_name):
    """Check if a package is available for import."""
    # Handle package name mappings (PyPI name vs import name)
    import_mappings = {
        "pyyaml": "yaml",
        "pillow": "PIL",
        "beautifulsoup4": "bs4",
        "python-dateutil": "dateutil",
        "msgpack": "msgpack",
        "protobuf": "google.protobuf",
        "pycryptodome": "Crypto",
        "pyserial": "serial",
        "python-magic": "magic",
        "opencv-python": "cv2",
        "scikit-learn": "sklearn",
        "matplotlib": "matplotlib.pyplot",
    }

    import_name = import_mappings.get(package_name.lower(), package_name)

    try:
        importlib.import_module(import_name)
        return True
    except ImportError:
        # Try alternative import patterns
        alternatives = [
            package_name.replace("-", "_"),
            package_name.replace("_", "-"),
            package_name.lower(),
        ]

        for alt_name in alternatives:
            try:
                importlib.import_module(alt_name)
                return True
            except ImportError:
                continue

        return False


def install_requirements(requirements_file):
    """Install requirements using pip."""
    print(f"\n📦 Installing requirements from {requirements_file}...")

    try:
        # Use current Python interpreter to ensure we install to the right environment
        cmd = [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)]

        # Check if we're in a virtual environment
        if hasattr(sys, "real_prefix") or (
            hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
        ):
            print("🐍 Detected virtual environment")
        else:
            print(
                "⚠️  Installing to system Python (consider using a virtual environment)"
            )
            # Ask for confirmation for system-wide install
            if os.getenv("PCILEECH_AUTO_INSTALL") != "1":
                confirm = input("Install to system Python? [y/N]: ").strip().lower()
                if confirm not in ("y", "yes"):
                    print(
                        "Aborted. Please use a virtual environment or install manually."
                    )
                    sys.exit(1)
            cmd.append("--user")  # Install to user directory for safety

        # Run pip install
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)

        if result.returncode == 0:
            print("✅ Requirements installed successfully")
            return True
        else:
            print(f"❌ Failed to install requirements:")
            print(f"   stdout: {result.stdout}")
            print(f"   stderr: {result.stderr}")
            print(f"\nTry installing manually:")
            print(f"   pip install -r {requirements_file}")
            return False

    except FileNotFoundError:
        print("❌ pip not found. Please install pip first.")
        return False
    except Exception as e:
        print(f"❌ Error installing requirements: {e}")
        return False


def check_critical_imports():
    """Check for imports that are absolutely required for basic functionality."""
    critical_packages = {
        "textual": "TUI functionality (install with: pip install textual)",
        "rich": "Rich text display (install with: pip install rich)",
        "psutil": "System information (install with: pip install psutil)",
    }

    missing_critical = []

    for package, description in critical_packages.items():
        if not is_package_available(package):
            missing_critical.append((package, description))

    return missing_critical


def safe_import_with_fallback(module_name, fallback_msg=None):
    """Safely import a module with a helpful error message."""
    try:
        return importlib.import_module(module_name)
    except ImportError as e:
        if fallback_msg:
            print(f"❌ {fallback_msg}")
        else:
            print(f"❌ Required module '{module_name}' not available")
            print(f"   Install with: pip install {module_name}")
        raise RequirementsError(f"Missing required module: {module_name}") from e


# Early requirements check before any other imports
if __name__ == "__main__":
    # Check requirements before proceeding
    try:
        requirements_ok = check_and_install_requirements()

        # Check critical packages that might not be in requirements.txt
        missing_critical = check_critical_imports()
        if missing_critical:
            print("\n❌ Critical packages missing:")
            for package, description in missing_critical:
                print(f"   - {package}: {description}")

            if not requirements_ok:
                print("\nPlease install missing packages and try again.")
                sys.exit(1)

    except KeyboardInterrupt:
        print("\n⚠️  Installation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error checking requirements: {e}")
        sys.exit(1)


# Import our custom utilities (after requirements check)
try:
    from src.error_utils import format_concise_error, log_error_with_root_cause
    from src.log_config import get_logger, setup_logging
    from src.string_utils import (
        log_error_safe,
        log_info_safe,
        log_warning_safe,
        safe_format,
    )
except ImportError as e:
    print(f"❌ Failed to import PCILeech modules: {e}")
    print("Make sure you're running from the PCILeech project directory")
    sys.exit(1)


def get_available_boards():
    """Get list of available board configurations."""
    try:
        from src.device_clone.board_config import list_supported_boards

        boards = list_supported_boards()
        if not boards:
            return [
                "pcileech_35t325_x4",
                "pcileech_75t484_x1",
                "pcileech_100t484_x1",
            ]
        return sorted(boards)
    except Exception:
        return [
            "pcileech_35t325_x4",
            "pcileech_75t484_x1",
            "pcileech_100t484_x1",
        ]


def check_sudo():
    """Check if running as root and warn if not."""
    logger = get_logger(__name__)
    if os.geteuid() != 0:
        log_warning_safe(
            logger,
            "PCILeech requires root privileges for hardware access.",
            prefix="SUDO",
        )
        log_warning_safe(logger, "Please run with sudo or as root user.", prefix="SUDO")
        return False
    return True


def check_vfio_requirements():
    """Check if VFIO modules are loaded and rebuild constants."""
    logger = get_logger(__name__)
    try:
        # Check if VFIO modules are loaded
        with open("/proc/modules", "r") as f:
            modules = f.read()
            if "vfio " not in modules or "vfio_pci " not in modules:
                log_warning_safe(logger, "VFIO modules not loaded. Run:", prefix="VFIO")
                log_warning_safe(logger, "  sudo modprobe vfio vfio-pci", prefix="VFIO")
                return False
    except FileNotFoundError:
        # /proc/modules not available, skip check
        pass

    # Always rebuild VFIO constants to ensure they match the current kernel
    log_info_safe(
        logger, "Rebuilding VFIO constants for current kernel...", prefix="VFIO"
    )
    if not rebuild_vfio_constants():
        log_warning_safe(
            logger,
            "VFIO constants rebuild failed - may cause ioctl errors",
            prefix="VFIO",
        )

    return True


def rebuild_vfio_constants():
    """Rebuild VFIO constants using the build script."""
    logger = get_logger(__name__)
    try:
        result = subprocess.run(
            ["./build_vfio_constants.sh"],
            capture_output=True,
            text=True,
            cwd=project_root,
            timeout=60,
        )

        if result.returncode == 0:
            log_info_safe(logger, "VFIO constants rebuilt successfully", prefix="VFIO")
            return True
        else:
            log_warning_safe(
                logger,
                "VFIO constants rebuild failed: {error}",
                prefix="VFIO",
                error=result.stderr,
            )
            return False

    except subprocess.TimeoutExpired:
        log_warning_safe(logger, "VFIO constants rebuild timed out", prefix="VFIO")
        return False
    except Exception as e:
        log_warning_safe(
            logger, "VFIO constants rebuild error: {error}", prefix="VFIO", error=str(e)
        )
        return False


def create_parser():
    """Create the main argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        prog="pcileech",
        description="PCILeech Firmware Generator - Unified Entry Point",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  build          Build firmware (CLI mode)
  tui            Launch interactive TUI
  flash          Flash firmware to device
  check          Check VFIO configuration and ACS bypass requirements
  donor-template Generate donor info template
  version        Show version information

Examples:
  # Interactive TUI mode
  sudo python3 pcileech.py tui

  # CLI build mode
  sudo python3 pcileech.py build --bdf 0000:03:00.0 --board pcileech_35t325_x1

  # Check VFIO configuration
  sudo python3 pcileech.py check --device 0000:03:00.0

  # Flash firmware
  sudo python3 pcileech.py flash firmware.bin
  
  # Generate donor template
  sudo python3 pcileech.py donor-template --save-to my_device.json

Environment Variables:
  PCILEECH_AUTO_INSTALL=1    Automatically install missing dependencies
        """,
    )

    # Add global options
    parser.add_argument(
        "--version", action="version", version="PCILeech Firmware Generator v0.7.4"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )
    parser.add_argument(
        "--quiet", "-q", action="store_true", help="Suppress non-error messages"
    )
    parser.add_argument(
        "--skip-requirements-check",
        action="store_true",
        help="Skip automatic requirements checking",
    )

    # Create subparsers for different modes
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Build command (CLI mode)
    build_parser = subparsers.add_parser("build", help="Build firmware (CLI mode)")
    build_parser.add_argument(
        "--bdf", required=True, help="PCI Bus:Device.Function (e.g., 0000:03:00.0)"
    )
    build_parser.add_argument(
        "--board",
        required=True,
        choices=get_available_boards(),
        help="Target board configuration",
    )
    build_parser.add_argument(
        "--advanced-sv",
        action="store_true",
        help="Enable advanced SystemVerilog features",
    )
    build_parser.add_argument(
        "--enable-variance", action="store_true", help="Enable manufacturing variance"
    )
    build_parser.add_argument(
        "--build-dir", default="build", help="Directory for generated firmware files"
    )
    build_parser.add_argument(
        "--generate-donor-template",
        help="Generate donor info JSON template alongside build artifacts",
    )
    build_parser.add_argument(
        "--donor-template",
        help="Use donor info JSON template to override discovered values",
    )
    build_parser.add_argument(
        "--device-type",
        choices=["generic", "network", "storage", "audio", "graphics"],
        default="generic",
        help="Override device type detection (default: auto-detect from class code)",
    )
    build_parser.add_argument(
        "--vivado-path",
        help="Manual path to Vivado installation directory (e.g., /tools/Xilinx/2025.1/Vivado)",
    )
    build_parser.add_argument(
        "--vivado-jobs",
        type=int,
        default=4,
        help="Number of parallel jobs for Vivado builds (default: 4)",
    )
    build_parser.add_argument(
        "--vivado-timeout",
        type=int,
        default=3600,
        help="Timeout for Vivado operations in seconds (default: 3600)",
    )

    # TUI command
    tui_parser = subparsers.add_parser("tui", help="Launch interactive TUI")
    tui_parser.add_argument("--profile", help="Load configuration profile on startup")

    # Flash command
    flash_parser = subparsers.add_parser("flash", help="Flash firmware to device")
    flash_parser.add_argument("firmware", help="Path to firmware file")
    flash_parser.add_argument("--board", help="Board type for flashing")
    flash_parser.add_argument("--device", help="USB device for flashing")

    # Check command (VFIO)
    check_parser = subparsers.add_parser(
        "check", help="Check VFIO configuration and ACS bypass requirements"
    )
    check_parser.add_argument("--device", help="Specific device to check (BDF format)")
    check_parser.add_argument(
        "--interactive", "-i", action="store_true", help="Interactive remediation mode"
    )
    check_parser.add_argument(
        "--fix", action="store_true", help="Attempt to fix issues automatically"
    )

    # Version command
    subparsers.add_parser("version", help="Show version information")

    # Donor template command
    donor_parser = subparsers.add_parser(
        "donor-template", help="Generate donor info template"
    )
    donor_parser.add_argument(
        "--save-to",
        default="donor_info_template.json",
        help="File path to save template (default: donor_info_template.json)",
    )
    donor_parser.add_argument(
        "--compact",
        action="store_true",
        help="Generate compact JSON without indentation",
    )
    donor_parser.add_argument(
        "--blank",
        action="store_true",
        help="Generate minimal template with only essential fields",
    )
    donor_parser.add_argument(
        "--bdf", help="Pre-fill template with device info from specified BDF"
    )
    donor_parser.add_argument("--validate", help="Validate an existing donor info file")

    return parser


def main():
    """Main entry point."""
    # Parse args early to check for skip flag
    parser = create_parser()
    args = parser.parse_args()

    # Skip requirements check if requested
    if not args.skip_requirements_check:
        try:
            check_and_install_requirements()
        except RequirementsError:
            return 1

    # Setup logging with our custom configuration
    if args.verbose:
        setup_logging(level=logging.DEBUG)
    elif args.quiet:
        setup_logging(level=logging.ERROR)
    else:
        setup_logging(level=logging.INFO)

    logger = get_logger(__name__)

    # Check sudo requirements for hardware operations
    if args.command in ["build", "check"] and not check_sudo():
        log_error_safe(
            logger, "Root privileges required for hardware operations.", prefix="MAIN"
        )
        return 1

    # Check VFIO requirements for build operations
    if args.command == "build" and not check_vfio_requirements():
        log_error_safe(
            logger,
            "Run 'sudo python3 pcileech.py check' to validate VFIO setup.",
            prefix="MAIN",
        )
        return 1

    # Route to appropriate handler with safe imports
    try:
        if args.command == "build":
            return handle_build(args)
        elif args.command == "tui":
            return handle_tui(args)
        elif args.command == "flash":
            return handle_flash(args)
        elif args.command == "check":
            return handle_check(args)
        elif args.command == "version":
            return handle_version(args)
        elif args.command == "donor-template":
            return handle_donor_template(args)
        else:
            # No command specified, show help
            parser.print_help()
            return 1
    except RequirementsError:
        return 1


def handle_build(args):
    """Handle CLI build mode."""
    logger = get_logger(__name__)
    try:
        # Import and use the existing CLI build functionality
        from src.cli.cli import main as cli_main

        log_info_safe(
            logger,
            "Starting build for device {bdf} on board {board}",
            prefix="BUILD",
            bdf=args.bdf,
            board=args.board,
        )

        # Convert arguments to CLI format
        cli_args = ["build", "--bdf", args.bdf, "--board", args.board]

        if args.advanced_sv:
            cli_args.append("--advanced-sv")
        if args.enable_variance:
            cli_args.append("--enable-variance")

        if args.generate_donor_template:
            cli_args.extend(["--output-template", args.generate_donor_template])

        if args.donor_template:
            cli_args.extend(["--donor-template", args.donor_template])

        # Pass device type if specified and not the default
        if hasattr(args, "device_type") and args.device_type != "generic":
            cli_args.extend(["--device-type", args.device_type])

        # Run the CLI
        return cli_main(cli_args)

    except ImportError as e:
        log_error_safe(
            logger, "Failed to import CLI module: {error}", prefix="BUILD", error=str(e)
        )
        log_error_safe(
            logger, "Make sure all dependencies are installed", prefix="BUILD"
        )
        return 1
    except Exception as e:
        from src.error_utils import log_error_with_root_cause

        log_error_with_root_cause(logger, "Build failed", e)
        return 1


def handle_tui(args):
    """Handle TUI mode."""
    logger = get_logger(__name__)
    try:
        # Check if Textual is available with helpful error
        textual = safe_import_with_fallback(
            "textual",
            "Textual framework not installed. Install with: pip install textual rich psutil",
        )

        # Import and run the TUI application
        from src.tui.main import PCILeechTUI

        log_info_safe(logger, "Launching interactive TUI", prefix="TUI")
        app = PCILeechTUI()
        app.run()
        return 0

    except RequirementsError:
        return 1
    except KeyboardInterrupt:
        log_info_safe(logger, "TUI application interrupted by user", prefix="TUI")
        return 1
    except Exception as e:
        from src.error_utils import log_error_with_root_cause

        log_error_with_root_cause(logger, "TUI failed", e)
        return 1


def handle_flash(args):
    """Handle firmware flashing."""
    logger = get_logger(__name__)
    try:
        # Check if firmware file exists
        firmware_path = Path(args.firmware)
        if not firmware_path.exists():
            log_error_safe(
                logger,
                "Firmware file not found: {path}",
                prefix="FLASH",
                path=firmware_path,
            )
            return 1

        log_info_safe(
            logger, "Flashing firmware: {path}", prefix="FLASH", path=firmware_path
        )

        # Try to use the flash utility
        try:
            from src.cli.flash import flash_firmware

            flash_firmware(firmware_path)
        except ImportError:
            # Fallback to direct usbloader if available
            result = subprocess.run(
                ["usbloader", "-f", str(firmware_path)], capture_output=True, text=True
            )
            if result.returncode != 0:
                log_error_safe(
                    logger, "Flash failed: {error}", prefix="FLASH", error=result.stderr
                )
                return 1
            log_info_safe(
                logger,
                "Successfully flashed {path}",
                prefix="FLASH",
                path=firmware_path,
            )

        return 0

    except Exception as e:
        from src.error_utils import log_error_with_root_cause

        log_error_with_root_cause(logger, "Flash failed", e)
        return 1


def handle_check(args):
    """Handle VFIO checking."""
    logger = get_logger(__name__)
    try:
        # Import the VFIO diagnostics functionality
        from pathlib import Path

        from src.cli.vfio_diagnostics import (
            Diagnostics,
            Status,
            remediation_script,
            render,
        )

        log_info_safe(
            logger,
            "Running VFIO diagnostics{device}",
            prefix="CHECK",
            device=f" for device {args.device}" if args.device else "",
        )

        # Create diagnostics instance and run checks
        diag = Diagnostics(args.device)
        report = diag.run()

        # Render the report
        render(report)

        # Handle fix option
        if args.fix:
            if report.overall == Status.OK:
                log_info_safe(
                    logger,
                    "✅ System already VFIO-ready - nothing to do",
                    prefix="CHECK",
                )
                return 0

            # Generate remediation script
            script_text = remediation_script(report)
            temp = Path("/tmp/vfio_fix.sh")
            temp.write_text(script_text)
            temp.chmod(0o755)

            log_info_safe(
                logger,
                "📝 Remediation script written to {path}",
                prefix="CHECK",
                path=temp,
            )

            if args.interactive:
                confirm = input("Run remediation script now? [y/N]: ").strip().lower()
                if confirm not in ("y", "yes"):
                    log_info_safe(logger, "Aborted.", prefix="CHECK")
                    return 1

            log_info_safe(
                logger,
                "Executing remediation script (requires root)...",
                prefix="CHECK",
            )
            try:
                subprocess.run(["sudo", str(temp)], check=True)

                # Re-run diagnostics after remediation
                log_info_safe(
                    logger,
                    "Re-running diagnostics after remediation...",
                    prefix="CHECK",
                )
                new_report = Diagnostics(args.device).run()
                render(new_report)
                return 0 if new_report.can_proceed else 1
            except subprocess.CalledProcessError as e:
                log_error_safe(
                    logger, "Script failed: {error}", prefix="CHECK", error=str(e)
                )
                return 1

        # Exit with appropriate code
        return 0 if report.can_proceed else 1

    except ImportError as e:
        log_error_safe(logger, "❌ VFIO diagnostics module not found.", prefix="CHECK")
        log_error_safe(
            logger,
            "Please ensure you're running this from the PCILeech project directory.",
            prefix="CHECK",
        )
        log_error_safe(logger, "Details: {error}", prefix="CHECK", error=str(e))
        return 1
    except Exception as e:
        from src.error_utils import log_error_with_root_cause

        log_error_with_root_cause(logger, "VFIO check failed", e)
        import traceback

        if logger.isEnabledFor(logging.DEBUG):
            traceback.print_exc()
        return 1


def handle_version(args):
    """Handle version information."""
    logger = get_logger(__name__)
    log_info_safe(logger, "PCILeech Firmware Generator v0.7.4", prefix="VERSION")
    log_info_safe(logger, "Copyright (c) 2024 PCILeech Project", prefix="VERSION")
    log_info_safe(logger, "Licensed under MIT License", prefix="VERSION")

    # Show additional version info
    try:
        import pkg_resources

        version = pkg_resources.get_distribution("pcileechfwgenerator").version
        log_info_safe(
            logger, "Package version: {version}", prefix="VERSION", version=version
        )
    except:
        pass

    return 0


def handle_donor_template(args):
    """Handle donor template generation."""
    logger = get_logger(__name__)
    try:
        from src.device_clone.donor_info_template import DonorInfoTemplateGenerator

        # If validate flag is set, validate the file instead
        if args.validate:
            try:
                validator = DonorInfoTemplateGenerator()
                is_valid, errors = validator.validate_template_file(args.validate)
                if is_valid:
                    log_info_safe(
                        logger,
                        "✓ Template file '{file}' is valid",
                        prefix="DONOR",
                        file=args.validate,
                    )
                    return 0
                else:
                    log_error_safe(
                        logger,
                        "✗ Template file '{file}' has errors:",
                        prefix="DONOR",
                        file=args.validate,
                    )
                    for error in errors:
                        log_error_safe(
                            logger, "  - {error}", prefix="DONOR", error=error
                        )
                    return 1
            except Exception as e:
                from src.error_utils import log_error_with_root_cause

                log_error_with_root_cause(logger, "Error validating template", e)
                return 1

        # Generate template
        generator = DonorInfoTemplateGenerator()

        # If BDF is specified, try to pre-fill with device info
        if args.bdf:
            log_info_safe(
                logger,
                "Generating template with device info from {bdf}...",
                prefix="DONOR",
                bdf=args.bdf,
            )
            try:
                template = generator.generate_template_from_device(args.bdf)
                # Check if we actually got device info
                if template["device_info"]["identification"]["vendor_id"] is None:
                    log_error_safe(
                        logger,
                        "Failed to read device information from {bdf}",
                        prefix="DONOR",
                        bdf=args.bdf,
                    )
                    log_error_safe(logger, "Possible causes:", prefix="DONOR")
                    log_error_safe(logger, "  - Device does not exist", prefix="DONOR")
                    log_error_safe(
                        logger,
                        "  - Insufficient permissions (try with sudo)",
                        prefix="DONOR",
                    )
                    log_error_safe(
                        logger, "  - lspci command not available", prefix="DONOR"
                    )
                    return 1
            except Exception as e:
                from src.error_utils import log_error_with_root_cause

                log_error_with_root_cause(logger, "Could not read device info", e)
                return 1
        elif args.blank:
            # Generate minimal template
            template = generator.generate_minimal_template()
            log_info_safe(
                logger, "Generating minimal donor info template...", prefix="DONOR"
            )
        else:
            # Generate full template
            template = generator.generate_blank_template()

        # Save the template
        generator.save_template_dict(
            template, Path(args.save_to), pretty=not args.compact
        )
        log_info_safe(
            logger,
            "✓ Donor info template saved to: {file}",
            prefix="DONOR",
            file=args.save_to,
        )

        if args.bdf:
            log_info_safe(
                logger, "Template pre-filled with device information.", prefix="DONOR"
            )
            log_info_safe(
                logger, "Please review and complete any missing fields.", prefix="DONOR"
            )
        else:
            log_info_safe(logger, "Next steps:", prefix="DONOR")
            log_info_safe(
                logger,
                "1. Fill in the device-specific values in the template",
                prefix="DONOR",
            )
            log_info_safe(
                logger,
                "2. Run behavioral profiling to capture timing data",
                prefix="DONOR",
            )
            log_info_safe(
                logger,
                "3. Use the completed template for advanced device cloning",
                prefix="DONOR",
            )

        return 0

    except Exception as e:
        from src.error_utils import log_error_with_root_cause

        log_error_with_root_cause(logger, "Failed to generate donor template", e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
