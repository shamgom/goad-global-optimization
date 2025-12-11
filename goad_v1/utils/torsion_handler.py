"""
Torsion handling for molecular optimization in GOAD v1.0

Detects rotatable bonds and applies torsion angles to molecules
"""

import numpy as np
from ase import Atoms
from typing import List, Tuple, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class TorsionHandler:
    """Detect and manipulate molecular torsions"""

    def __init__(self, molecule: Atoms):
        """
        Initialize torsion handler.

        Args:
            molecule: ASE Atoms object (molecule)
        """
        self.molecule = molecule
        self.rotatable_bonds = []
        self.torsion_angles = []
        self.n_torsions = 0

        # Detect torsions using RDKit if available
        self._detect_torsions_rdkit()

    def _detect_torsions_rdkit(self):
        """
        Detect rotatable bonds using RDKit.

        Identifies bonds that can rotate (not in rings, not triple bonds)
        """
        try:
            from rdkit import Chem
            from rdkit.Chem import Descriptors, Lipinski
            from ase.io import write
            import tempfile
            import os

            # Convert ASE Atoms to temporary file
            with tempfile.NamedTemporaryFile(suffix='.sdf', delete=False) as tmp:
                tmp_file = tmp.name

            try:
                write(tmp_file, self.molecule)

                # Load with RDKit
                mol = Chem.SDMolFromFile(tmp_file)
                if mol is None:
                    logger.warning("Could not parse molecule with RDKit")
                    return

                # Find rotatable bonds
                rotatable_bonds = []

                for bond in mol.GetBonds():
                    # Skip if bond is in ring
                    if bond.IsInRing():
                        continue

                    # Skip double/triple bonds
                    if bond.GetBondType() != Chem.BondType.SINGLE:
                        continue

                    begin_atom = bond.GetBeginAtomIdx()
                    end_atom = bond.GetEndAtomIdx()

                    # Skip bonds to hydrogen
                    begin_atom_obj = mol.GetAtomWithIdx(begin_atom)
                    end_atom_obj = mol.GetAtomWithIdx(end_atom)

                    if begin_atom_obj.GetAtomicNum() == 1 or end_atom_obj.GetAtomicNum() == 1:
                        continue

                    # Skip if either atom has only 1 neighbor
                    if len(begin_atom_obj.GetNeighbors()) < 2 or len(end_atom_obj.GetNeighbors()) < 2:
                        continue

                    rotatable_bonds.append((begin_atom, end_atom))

                self.rotatable_bonds = rotatable_bonds
                self.n_torsions = len(rotatable_bonds)

                logger.info(f"Detected {self.n_torsions} rotatable bonds:")
                for i, (b, e) in enumerate(rotatable_bonds):
                    logger.info(f"  Torsion {i}: atoms {b}-{e}")

                # Initialize torsion angles (0 degrees)
                self.torsion_angles = [0.0] * self.n_torsions

            finally:
                # Clean up temp file
                if os.path.exists(tmp_file):
                    os.remove(tmp_file)

        except ImportError:
            logger.warning("RDKit not available, torsion detection disabled")
            self.rotatable_bonds = []
            self.n_torsions = 0
        except Exception as e:
            logger.warning(f"Error detecting torsions: {e}")
            self.rotatable_bonds = []
            self.n_torsions = 0

    def apply_torsions(self, molecule_copy: Atoms, torsion_angles: List[float]) -> Atoms:
        """
        Apply torsion angles to a molecule copy.

        Args:
            molecule_copy: Copy of molecule to rotate
            torsion_angles: List of torsion angles in degrees

        Returns:
            Modified molecule with torsions applied
        """
        if len(torsion_angles) != self.n_torsions:
            logger.warning(f"Torsion angle count mismatch: {len(torsion_angles)} vs {self.n_torsions}")
            return molecule_copy

        if self.n_torsions == 0:
            return molecule_copy

        # Apply each torsion
        for i, (torsion_angle, (bond_begin, bond_end)) in enumerate(
            zip(torsion_angles, self.rotatable_bonds)
        ):
            molecule_copy = self._apply_single_torsion(
                molecule_copy, bond_begin, bond_end, torsion_angle
            )

        return molecule_copy

    def _apply_single_torsion(self, atoms: Atoms, bond_begin: int, bond_end: int,
                             angle_degrees: float) -> Atoms:
        """
        Apply a single torsion rotation.

        Rotates atoms connected to bond_end around the bond_begin-bond_end axis.

        Args:
            atoms: Molecule to modify
            bond_begin: Index of first atom in bond
            bond_end: Index of second atom in bond
            angle_degrees: Rotation angle in degrees

        Returns:
            Modified molecule
        """
        # Convert angle to radians
        angle_rad = np.deg2rad(angle_degrees)

        positions = atoms.get_positions()

        # Get bond axis
        axis = positions[bond_end] - positions[bond_begin]
        axis = axis / np.linalg.norm(axis)

        # Find atoms connected to bond_end (excluding bond_begin)
        try:
            from ase.neighborlist import neighbor_list
            i, j = neighbor_list('ij', atoms, cutoff=1.6)

            # Find neighbors of bond_end
            neighbors_to_rotate = []
            for idx_pair in range(len(i)):
                if i[idx_pair] == bond_end and j[idx_pair] != bond_begin:
                    neighbors_to_rotate.append(j[idx_pair])
                elif j[idx_pair] == bond_end and i[idx_pair] != bond_begin:
                    neighbors_to_rotate.append(i[idx_pair])

        except:
            logger.warning("Could not determine connected atoms for torsion")
            return atoms

        # Build set of atoms to rotate (connected to bond_end)
        atoms_to_rotate = set(neighbors_to_rotate)
        to_check = list(neighbors_to_rotate)

        while to_check:
            current = to_check.pop(0)
            try:
                from ase.neighborlist import neighbor_list
                i, j = neighbor_list('ij', atoms, cutoff=1.6)

                for idx_pair in range(len(i)):
                    if i[idx_pair] == current and j[idx_pair] != bond_begin and j[idx_pair] != bond_end:
                        if j[idx_pair] not in atoms_to_rotate:
                            atoms_to_rotate.add(j[idx_pair])
                            to_check.append(j[idx_pair])
                    elif j[idx_pair] == current and i[idx_pair] != bond_begin and i[idx_pair] != bond_end:
                        if i[idx_pair] not in atoms_to_rotate:
                            atoms_to_rotate.add(i[idx_pair])
                            to_check.append(i[idx_pair])
            except:
                break

        # Apply rotation to selected atoms
        rotation_matrix = self._rotation_matrix_axis_angle(axis, angle_rad)

        for atom_idx in atoms_to_rotate:
            # Translate to bond_end as origin
            relative_pos = positions[atom_idx] - positions[bond_end]

            # Rotate
            rotated_pos = relative_pos @ rotation_matrix.T

            # Translate back
            positions[atom_idx] = rotated_pos + positions[bond_end]

        atoms.set_positions(positions)
        return atoms

    @staticmethod
    def _rotation_matrix_axis_angle(axis: np.ndarray, angle: float) -> np.ndarray:
        """
        Create rotation matrix from axis and angle (Rodrigues' formula).

        Args:
            axis: Unit vector (rotation axis)
            angle: Rotation angle in radians

        Returns:
            3x3 rotation matrix
        """
        cos_a = np.cos(angle)
        sin_a = np.sin(angle)

        # Skew-symmetric cross-product matrix
        K = np.array([
            [0, -axis[2], axis[1]],
            [axis[2], 0, -axis[0]],
            [-axis[1], axis[0], 0]
        ])

        # Rodrigues' rotation formula: R = I + sin(θ)K + (1-cos(θ))K²
        R = np.eye(3) + sin_a * K + (1 - cos_a) @ (K @ K)

        return R

    def get_info(self) -> Dict:
        """
        Get torsion information.

        Returns:
            Dictionary with torsion info
        """
        return {
            'n_torsions': self.n_torsions,
            'rotatable_bonds': self.rotatable_bonds,
            'current_angles': self.torsion_angles,
        }

    def get_torsion_range(self) -> Tuple[List[float], List[float]]:
        """
        Get torsion angle ranges.

        Returns:
            Tuple of (min_angles, max_angles) in degrees
        """
        # Torsions can rotate 0-360 degrees
        min_angles = [0.0] * self.n_torsions
        max_angles = [360.0] * self.n_torsions

        return min_angles, max_angles
