"""
Calculator management for GOAD v1.0

Handles different MatterSim calculator configurations
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class CalculatorManager:
    """Manage different ASE calculator configurations"""

    @staticmethod
    def get_mattersim_1m():
        """
        Get MatterSim 1M calculator (fastest, lower accuracy)

        Returns:
            MatterSim calculator object
        """
        try:
            from mattersim.forcefield import MatterSimCalculator

            logger.info("Loading MatterSim 1M calculator...")
            # MatterSimCalculator loads the default 1M model by default
            # Note: MatterSim may perform internal structure relaxation
            # Use get_potential_energy() for single-point calculations only
            calc = MatterSimCalculator()
            logger.info("✓ MatterSim 1M loaded successfully")
            return calc

        except Exception as e:
            logger.error(f"Could not load MatterSim 1M: {e}", exc_info=True)
            raise

    @staticmethod
    def get_mattersim_5m():
        """
        Get MatterSim 5M calculator (balanced speed/accuracy)

        Returns:
            MatterSim calculator object
        """
        try:
            from mattersim.forcefield import MatterSimCalculator

            logger.info("Loading MatterSim 5M calculator...")
            # Try to load 5M model - may not be available in all installations
            calc = MatterSimCalculator(model_name="mattersim-v1.0.0-5M")
            logger.info("✓ MatterSim 5M loaded successfully")
            return calc

        except Exception as e:
            logger.warning(f"MatterSim 5M not available, falling back to 1M: {e}")
            # Fall back to 1M
            return CalculatorManager.get_mattersim_1m()

    @staticmethod
    def get_mattersim_5m_d3():
        """
        Get MatterSim 5M calculator with D3 dispersion correction (highest accuracy)

        Returns:
            MatterSim calculator object
        """
        try:
            from mattersim.forcefield import MatterSimCalculator

            logger.info("Loading MatterSim 5M + D3 calculator...")
            # Try to load 5M with D3
            calc = MatterSimCalculator(model_name="mattersim-v1.0.0-5M", use_d3=True)
            logger.info("✓ MatterSim 5M + D3 loaded successfully")
            return calc

        except Exception as e:
            logger.warning(f"MatterSim 5M+D3 not available, falling back to 1M: {e}")
            # Fall back to 1M
            return CalculatorManager.get_mattersim_1m()

    @staticmethod
    def get_calculator(calculator_type: str = "1m"):
        """
        Get calculator by type string.

        Args:
            calculator_type: Type of calculator ("1m", "5m", "5m_d3")

        Returns:
            Calculator object

        Raises:
            ValueError: If invalid calculator type
        """
        calculator_type = calculator_type.lower().strip()

        if calculator_type == "1m":
            return CalculatorManager.get_mattersim_1m()
        elif calculator_type == "5m":
            return CalculatorManager.get_mattersim_5m()
        elif calculator_type == "5m_d3" or calculator_type == "5m+d3":
            return CalculatorManager.get_mattersim_5m_d3()
        else:
            raise ValueError(f"Unknown calculator type: {calculator_type}")

    @staticmethod
    def get_calculator_info(calculator_type: str) -> dict:
        """
        Get information about a calculator type.

        Args:
            calculator_type: Type of calculator

        Returns:
            Dictionary with info
        """
        info_map = {
            "1m": {
                "name": "MatterSim 1M",
                "description": "Fast, lower accuracy. Good for exploration.",
                "speed": "Fastest",
                "accuracy": "Lower",
                "dispersion": "No",
            },
            "5m": {
                "name": "MatterSim 5M",
                "description": "Balanced speed and accuracy. Recommended.",
                "speed": "Medium",
                "accuracy": "High",
                "dispersion": "No",
            },
            "5m_d3": {
                "name": "MatterSim 5M + D3",
                "description": "High accuracy with dispersion correction. Slowest but most accurate.",
                "speed": "Slower",
                "accuracy": "Highest",
                "dispersion": "Yes (D3)",
            },
        }

        return info_map.get(calculator_type.lower(), {})
