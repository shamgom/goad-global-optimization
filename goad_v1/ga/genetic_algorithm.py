"""
Improved Genetic Algorithm for GOAD v1.0

Surface atoms are completely fixed during GA optimization
Includes molecular torsions in the genome
"""

import numpy as np
from ase import Atoms
from ase.optimize import BFGS
from ase.constraints import FixAtoms
from typing import Dict, List, Optional, Tuple
import logging

from ..utils.torsion_handler import TorsionHandler

logger = logging.getLogger(__name__)


class GeneticAlgorithm:
    """
    Genetic Algorithm for molecular adsorption on surfaces.

    Key features for v1.0:
    - Surface atoms are COMPLETELY FIXED during GA
    - Only molecule position and orientation vary
    - Support for molecular torsions (future)
    """

    def __init__(self, surface: Atoms, molecule: Atoms, calculator,
                 surface_energy: float, molecule_energy: float,
                 n_fixed_layers: int = 1,
                 generations: int = 50, population_size: int = 30,
                 mutation_rate: float = 0.3, crossover_rate: float = 0.7,
                 elite_size: int = 5, verbose: bool = True):
        """
        Initialize GA.

        Args:
            surface: Surface structure
            molecule: Molecule structure
            calculator: ASE calculator
            surface_energy: Reference energy of surface
            molecule_energy: Reference energy of molecule
            n_fixed_layers: Number of layers to keep fixed (info only, all surface fixed in GA)
            generations: Number of generations
            population_size: Population size
            mutation_rate: Mutation rate (0-1)
            crossover_rate: Crossover rate (0-1)
            elite_size: Number of elite individuals to preserve
            verbose: Print progress
        """
        self.surface = surface
        self.molecule = molecule
        self.calculator = calculator
        self.surface_energy = surface_energy
        self.molecule_energy = molecule_energy
        self.n_fixed_layers = n_fixed_layers

        # GA parameters
        self.generations = generations
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.elite_size = elite_size
        self.verbose = verbose

        # Surface properties
        self._analyze_surface()

        # Torsion handling
        self.torsion_handler = TorsionHandler(molecule)
        self.n_torsions = self.torsion_handler.n_torsions

        if self.n_torsions > 0:
            logger.info(f"Molecule has {self.n_torsions} rotatable bonds")
        else:
            logger.info("Molecule has no rotatable bonds (rigid)")

        # Population and history
        self.population = []
        self.fitness_history = []
        self.best_individual = None
        self.best_energy = float('inf')

        # Search space parameters
        self.search_radius = 10.0  # Lateral search radius (Angstrom)
        self.max_height = 8.0  # Maximum height above surface
        self.surface_buffer = 1.5  # Minimum distance from surface

    def _analyze_surface(self):
        """Analyze surface properties"""
        positions = self.surface.get_positions()
        z_coords = positions[:, 2]

        self.surface_z_min = z_coords.min()
        self.surface_z_max = z_coords.max()
        self.surface_center_xy = positions[:, :2].mean(axis=0)

        logger.info(f"Surface Z range: {self.surface_z_min:.2f} - {self.surface_z_max:.2f} Å")
        logger.info(f"Surface center (XY): {self.surface_center_xy}")

    def run(self) -> Dict:
        """
        Run the genetic algorithm.

        Returns:
            Dictionary with results
        """
        logger.info("=" * 60)
        logger.info("GENETIC ALGORITHM - GOAD v1.0")
        logger.info("=" * 60)
        logger.info(f"Population: {self.population_size}")
        logger.info(f"Generations: {self.generations}")
        logger.info(f"Surface: COMPLETELY FIXED (all atoms)")
        logger.info(f"Molecule: FREE TO MOVE")
        logger.info(f"\nGenome composition:")
        logger.info(f"  Position (X, Y, Z):     3 genes")
        logger.info(f"  Orientation (α, β, γ): 3 genes")
        logger.info(f"  Torsions:               {self.n_torsions} genes")
        logger.info(f"  Total genes per individual: {6 + self.n_torsions}")
        logger.info("=" * 60 + "\n")

        # Initialize population
        self._initialize_population()

        # Main GA loop
        for gen in range(self.generations):
            # Evaluate fitness
            self._evaluate_population()

            # Log progress
            if self.verbose:
                best_gen = min(self.fitness_history[-self.population_size:])
                logger.info(f"Gen {gen+1}/{self.generations} | "
                          f"Best: {best_gen:.4f} eV | "
                          f"Overall best: {self.best_energy:.4f} eV")

            # Selection, crossover, mutation
            self._selection_crossover_mutation()

        logger.info("\n" + "=" * 60)
        logger.info("GA COMPLETED")
        logger.info("=" * 60)

        return self._get_results()

    def _initialize_population(self):
        """Initialize random population"""
        logger.info("Initializing population...")

        for i in range(self.population_size):
            # Random molecule position above surface
            x = self.surface_center_xy[0] + np.random.uniform(-self.search_radius, self.search_radius)
            y = self.surface_center_xy[1] + np.random.uniform(-self.search_radius, self.search_radius)
            z = self.surface_z_max + np.random.uniform(self.surface_buffer, self.max_height)

            # Random orientation (Euler angles in degrees)
            euler_angles = np.random.uniform(0, 360, 3)

            # Random torsion angles (0-360 degrees)
            torsion_angles = np.random.uniform(0, 360, self.n_torsions)

            individual = {
                'position': np.array([x, y, z]),
                'orientation': np.array(euler_angles),
                'torsions': np.array(torsion_angles),
                'energy': None,
                'structure': None
            }

            self.population.append(individual)

    def _evaluate_population(self):
        """Evaluate fitness of all individuals"""
        for individual in self.population:
            if individual['energy'] is None:
                individual['energy'] = self._calculate_energy(individual)
                self.fitness_history.append(individual['energy'])

                # Update best
                if individual['energy'] < self.best_energy:
                    self.best_energy = individual['energy']
                    self.best_individual = individual.copy()

    def _calculate_energy(self, individual: Dict) -> float:
        """
        Calculate energy of a molecule placement.

        Args:
            individual: Individual with position and orientation

        Returns:
            Energy value
        """
        try:
            # Create system: surface + positioned molecule
            system = self._create_system(individual)

            # Fix all surface atoms
            surface_atoms_count = len(self.surface)
            fixed_indices = list(range(surface_atoms_count))
            system.set_constraint(FixAtoms(indices=fixed_indices))

            # Set calculator
            system.set_calculator(self.calculator)

            # Calculate energy
            energy = system.get_potential_energy()

            # Calculate adsorption energy
            e_ads = energy - (self.surface_energy + self.molecule_energy)

            individual['structure'] = system

            return e_ads

        except Exception as e:
            logger.warning(f"Energy calculation failed: {e}")
            return 1000.0  # Penalty for failed calculation

    def _create_system(self, individual: Dict) -> Atoms:
        """
        Create combined system of surface + positioned molecule.

        Args:
            individual: Individual with position, orientation, and torsions

        Returns:
            Combined Atoms object
        """
        surface_copy = self.surface.copy()
        molecule_copy = self.molecule.copy()

        # Apply torsions FIRST (before positioning)
        if self.n_torsions > 0:
            molecule_copy = self.torsion_handler.apply_torsions(
                molecule_copy,
                individual['torsions']
            )

        # Position molecule
        molecule_copy.translate(individual['position'] - molecule_copy.get_center_of_mass())

        # Apply rotation
        self._apply_rotation(molecule_copy, individual['orientation'])

        # Combine
        system = surface_copy + molecule_copy

        return system

    def _apply_rotation(self, atoms: Atoms, euler_angles: np.ndarray):
        """
        Apply rotation to atoms using Euler angles.

        Args:
            atoms: Atoms to rotate
            euler_angles: Euler angles in degrees [alpha, beta, gamma]
        """
        from ase.geometry.geometry import get_distances

        # Convert to radians
        angles_rad = np.deg2rad(euler_angles)

        # Rotation matrices
        alpha, beta, gamma = angles_rad

        # Rx (rotation around x)
        Rx = np.array([
            [1, 0, 0],
            [0, np.cos(alpha), -np.sin(alpha)],
            [0, np.sin(alpha), np.cos(alpha)]
        ])

        # Ry (rotation around y)
        Ry = np.array([
            [np.cos(beta), 0, np.sin(beta)],
            [0, 1, 0],
            [-np.sin(beta), 0, np.cos(beta)]
        ])

        # Rz (rotation around z)
        Rz = np.array([
            [np.cos(gamma), -np.sin(gamma), 0],
            [np.sin(gamma), np.cos(gamma), 0],
            [0, 0, 1]
        ])

        # Combined rotation matrix
        R = Rz @ Ry @ Rx

        # Center of mass
        com = atoms.get_center_of_mass()

        # Rotate around COM
        positions = atoms.get_positions()
        relative_pos = positions - com
        rotated_pos = relative_pos @ R.T
        atoms.set_positions(rotated_pos + com)

    def _selection_crossover_mutation(self):
        """Selection, crossover, and mutation"""

        # Sort population by fitness
        self.population.sort(key=lambda x: x['energy'])

        # Keep elite
        new_population = self.population[:self.elite_size].copy()

        # Generate new individuals
        while len(new_population) < self.population_size:
            if np.random.random() < self.crossover_rate:
                # Crossover
                parent1 = self._select_parent()
                parent2 = self._select_parent()
                child = self._crossover(parent1, parent2)
            else:
                # Mutate elite
                parent = self._select_parent()
                child = self._mutate(parent.copy())

            new_population.append(child)

        self.population = new_population

    def _select_parent(self) -> Dict:
        """Select parent using tournament selection"""
        tournament_size = 5
        tournament = np.random.choice(len(self.population), tournament_size, replace=False)
        winner_idx = min(tournament, key=lambda i: self.population[i]['energy'])
        return self.population[winner_idx].copy()

    def _crossover(self, parent1: Dict, parent2: Dict) -> Dict:
        """Crossover two parents"""
        # 50% from parent1, 50% from parent2
        child = {
            'position': parent1['position'].copy(),
            'orientation': parent2['orientation'].copy(),
            'torsions': np.zeros(self.n_torsions),
            'energy': None,
            'structure': None
        }

        # Mix torsions
        for i in range(self.n_torsions):
            if np.random.random() < 0.5:
                child['torsions'][i] = parent1['torsions'][i]
            else:
                child['torsions'][i] = parent2['torsions'][i]

        return child

    def _mutate(self, individual: Dict) -> Dict:
        """Mutate an individual"""
        mutation_choice = np.random.random()

        if mutation_choice < 0.33:
            # Mutate position
            individual['position'] += np.random.normal(0, 0.5, 3)

        elif mutation_choice < 0.66:
            # Mutate orientation
            individual['orientation'] += np.random.normal(0, 10, 3)
            individual['orientation'] = individual['orientation'] % 360

        else:
            # Mutate torsions
            for i in range(self.n_torsions):
                if np.random.random() < 0.5:
                    individual['torsions'][i] += np.random.normal(0, 20)
                    individual['torsions'][i] = individual['torsions'][i] % 360

        individual['energy'] = None
        individual['structure'] = None

        return individual

    def _get_results(self) -> Dict:
        """Get GA results"""
        results = {
            'best_individual': self.best_individual,
            'best_energy': self.best_energy,
            'best_structure': self.best_individual['structure'] if self.best_individual else None,
            'fitness_history': self.fitness_history,
            'generations': self.generations,
            'population_size': self.population_size,
        }

        logger.info(f"Best E_ads found: {self.best_energy:.4f} eV")
        if self.best_individual:
            logger.info(f"Best position (Å): X={self.best_individual['position'][0]:.2f}, Y={self.best_individual['position'][1]:.2f}, Z={self.best_individual['position'][2]:.2f}")
            logger.info(f"Best orientation (°): α={self.best_individual['orientation'][0]:.1f}, β={self.best_individual['orientation'][1]:.1f}, γ={self.best_individual['orientation'][2]:.1f}")
            if self.n_torsions > 0:
                logger.info(f"Best torsions (°): {' '.join([f'{t:.1f}' for t in self.best_individual['torsions']])}")

        return results
