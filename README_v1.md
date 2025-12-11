````markdown
# GOAD v1 - Global Optimization with ASE Design

Advanced molecular adsorption optimization with intelligent layer control and multi-stage workflow.

## New Features in v1

✨ **Complete workflow redesign:**
- 4-step interactive workflow with separate windows for each phase
- Automatic surface type detection (Slab vs Porous)
- Intelligent layer analysis for slab structures
- User-selected fixed layer configuration

✨ **Improved accuracy:**
- Reference energies respect fixed layer constraints
- Full relaxation of reference structures (surface + molecule)
- Fixed layer preservation through entire workflow
- GA with completely fixed surface (no atomic movement)

✨ **Better control:**
- Choose how many layers to keep fixed
- Select between relaxation or single-point reference energies
- Optional final optimization step
- Timestamped results with detailed summaries

## Quick Start

### Installation

```bash
# 1. Create environment
conda create -n goad_v1 python=3.10
conda activate goad_v1

# 2. Install dependencies
conda install -c conda-forge ase numpy matplotlib
pip install mattersim

# 3. Navigate to directory
cd goad_v1
```

### Run GOAD v1

```bash
python3 run_goad_v1.py
```

## Workflow Overview

### Window 1: Structure Analysis
**Load and analyze your structures**

1. Click "Load Surface CIF" - select your surface file
2. Click "Load Molecule CIF" - select your molecule file
3. Click "Analyze Structures"
4. System detects surface type:
   - **SLAB:** Vacuum space above → shows layer analysis
   - **POROUS:** Atoms in all directions → feature in development
5. Select number of layers to keep fixed (bottom N layers)
6. Click "Next: Reference Energies"

**Output:**
- Surface and molecule properties
- Layer positions and composition
- Fixed layer configuration

### Window 2: Reference Energy Calculation
**Calculate baseline energies**

1. Choose mode:
   - **Relax (0-1000 steps):** Optimizes structures respecting constraints
   - **Single point:** Uses structures as-is
2. Click "Calculate References"
3. System calculates:
   - E_surface (relaxed, bottom N layers fixed)
   - E_molecule (fully relaxed)
4. Click "Next: Genetic Algorithm"

**Output:**
- E_surface and E_molecule reference values
- Relaxed structures ready for GA

### Window 3: Genetic Algorithm
**Optimize molecular adsorption**

1. Configure GA parameters (or use defaults)
2. Click "Run GA"
3. Monitor:
   - Energy evolution plot
   - Generation progress in log
   - Best structures found

**Key features:**
- Surface atoms: COMPLETELY FIXED
- Molecule: FREE (position, orientation, coordinates)
- Evaluates thousands of adsorption sites
- Finds optimal binding configuration

**Output:**
- Best E_adsorption energy
- Optimal position and orientation
- Energy convergence plot

### Window 4: Final Optimization
**Optional: Relax the best structure**

1. Choose:
   - **Optimize:** Full relaxation respecting fixed layers
   - **Use as final:** Keep GA result
2. Click "Execute"
3. System performs full BFGS relaxation
4. Click "Save Results & Exit"

**Output:**
- Optimized structure (CIF file)
- Energy summary
- Timestamped results directory

## Key Concepts

### Fixed Layers
- Bottom N atomic layers are kept completely fixed during:
  - Reference energy calculations
  - GA optimization
  - Final relaxation
- Simulates bulk behavior
- Reduces computational cost
- More realistic for surface chemistry

### Surface Type Detection
```
SLAB (Supported):
  - Vacuum space above surface
  - Molecule adsorbs from above
  - Layer analysis available

POROUS (Development):
  - Atoms in all directions
  - MOF, Zeolite, framework structures
  - Coming in future versions
```

### Adsorption Energy
```
E_adsorption = E_system - (E_surface + E_molecule)

Where:
- E_system = energy of surface + molecule combined
- E_surface = reference energy of surface alone
- E_molecule = reference energy of molecule alone
```

## Parameter Guide

### GA Parameters

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| Generations | 50 | 10-500 | Number of generations |
| Population | 30 | 10-200 | Population size |
| Mutation rate | 0.3 | 0.1-0.9 | Exploration rate |
| Crossover rate | 0.7 | 0.1-0.9 | Solution mixing rate |
| Elite size | 5 | 1-50 | Best individuals preserved |

### Optimization Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| Convergence (fmax) | 0.02 eV/Å | Force threshold |
| Max steps | 500 | Maximum optimization iterations |
| Fixed layers | User selected | Bottom N layers completely fixed |
| Optimizer | BFGS | Quasi-Newton method |

## Example Workflow

```
1. Load Cu(111) surface (3x3x4 slabs)
   → Detected: 4 atomic layers

2. Load H2O molecule

3. Analyze structures
   → Surface: 36 Cu atoms, Z = 0-2.6 Å
   → Molecule: 3 atoms (H2O)
   → Select to fix: 2 layers

4. Calculate references (relax mode, max 1000 steps)
   → E_surface = -2268.45 eV (2 layers fixed)
   → E_molecule = -14.32 eV (fully free)

5. Run GA (50 generations, 30 population)
   → Evaluates 1500 configurations
   → Best found: E_ads = -0.45 eV
   → Position: (12.3, 5.6, 2.8) Å
   → Orientation: (45°, 30°, 60°)

6. Final optimization (optional)
   → E_ads improved to: -0.52 eV
   → 2 layers still fixed
   → Surface structure preserved
````
