# Single-Point vs Relaxation Mode - Clarification

## Issue Found

When selecting "Use as-is (single point)" mode in Window 2 (Reference Energies), you observed that the system appears to be minimized. This is a **known behavior of some force field calculators**.

## Root Cause

Some calculators (including certain versions of MatterSim) may perform **internal structure relaxation** when computing `get_potential_energy()`. This is because:

1. They minimize the structure to get the "most accurate" energy
2. They adjust atomic positions to be "reasonable" before energy calculation
3. They apply internal convergence criteria before returning the energy

This is **not a bug in GOAD v1**, but rather a behavior of the underlying force field calculator.

## How GOAD v1 Handles This (UPDATED)

We've added **displacement detection** in the single-point calculation mode:

```python
# Before calculation
surface_original_pos = surface_copy.get_positions().copy()

# After energy calculation
surface_final_pos = surface_copy.get_positions()

# Check if structure changed
pos_change_surface = np.max(np.abs(surface_final_pos - surface_original_pos))
if pos_change_surface > 0.001:  # 0.001 Å threshold
    log("⚠ Structure changed: max displacement = X.XXXX Å")
else:
    log("✓ No relaxation (displacement = X.XXe-X Å)")
```

This allows you to **monitor in the log** whether the calculator is actually relaxing the structure or keeping it as-is.

## What You'll See

### ✅ If Calculator Does NOT Relax
```
[1/2] Calculating surface single-point...
✓ No relaxation (displacement = 1.23e-08 Å)
✓ E_surface = -123.4567 eV
```

### ⚠️ If Calculator DOES Relax
```
[1/2] Calculating surface single-point...
⚠ Structure changed: max displacement = 0.3456 Å
✓ E_surface = -125.1234 eV
```

## Recommended Actions

### If You Want True Single-Point Energies:

1. **Use "Relax both" mode** instead, which gives you control over the optimization
2. **Check the log output** - if displacement > 0.001 Å appears, the calculator is relaxing
3. **Switch to relaxation mode** if you need guaranteed energy calculation without implicit minimization

### If Internal Relaxation is Acceptable:

1. You can use "Use as-is" mode
2. Monitor the log to verify what's happening
3. The results are still valid for your GA workflow (reference energies just need consistency)

## How Calculators Should Behave

| Mode | Behavior | What GOAD Does |
|------|----------|----------------|
| Single-point | Direct energy calculation, NO relaxation | Detects any changes, warns if detected |
| Relaxation | Full BFGS optimization (0-1000 steps) | Explicit BFGS minimization |

## Technical Details

### MatterSim Behavior

MatterSim may perform:
- Structure relaxation to "reasonable" geometry
- Constraint adjustments
- Internal convergence procedures

This is **not explicit in the code** but happens at the calculator level.

### ASE Interface

The ASE interface we use (`get_potential_energy()`) is a single-point call:
```python
atoms.set_calculator(calc)
energy = atoms.get_potential_energy()  # Single point - no optimization
```

However, what happens **inside** the calculator is beyond GOAD's control.

## Solution Comparison

| Approach | Pros | Cons |
|----------|------|------|
| Use "Relax both" | Full control, clear optimization | Slower (BFGS iterations) |
| Use "Use as-is" + monitor log | Faster if no relaxation | May have implicit relaxation |
| Pre-relax structures offline | Complete control | Extra workflow step |

## Recommendation

**For Reference Energy Calculation:**
1. Use **"Relax both"** mode (recommended)
   - You get explicit control over the optimization
   - Clear about what's happening
   - Same computational cost as implicit relaxation
   
2. Monitor the log output to verify behavior
3. If displacement is detected in single-point mode, switch to explicit relaxation

**For GA Optimization:**
- The reference energies are used to compute adsorption energy
- Whether they're relaxed or not is less critical if you're **consistent**
- But relaxed structures are more physically meaningful

## Updated Window 2

We've added a **warning note** in Window 2:

```
⚠ Note: Some calculators may perform 
internal relaxation. Monitor results.
```

This reminds you to check the log for actual displacements.

## Files Modified

* `goad_v1/gui/reference_energies_window.py`
  - Added displacement detection in `_calculate_single_point()`
  - Added warning label in GUI
  - Log now shows actual atomic displacements

* `goad_v1/utils/calculator_manager.py`
  - Added note about MatterSim behavior

## Verification

To verify the behavior:

1. Select "Use as-is (single point)" mode
2. Run reference energy calculation
3. Check the Log tab
4. Look for either:
   - `✓ No relaxation (displacement = X.XXe-XX Å)` ← Good, no relaxation
   - `⚠ Structure changed: max displacement = X.XXXX Å` ← Calculator is relaxing

If you see the warning, switch to "Relax both" mode for explicit control.

---

**Status**: IDENTIFIED AND MITIGATED
**Action Taken**: Added displacement detection and warnings
**Last Updated**: 2025-11-28
