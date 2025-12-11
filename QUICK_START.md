# QUICK START — GOAD v1.0

This file explains the minimal steps to run the project locally.

1) Create and activate a Python environment (recommended):

```bash
# using conda (recommended, for RDKit compatibility):
conda create -n goad python=3.10 -y
conda activate goad

# or using venv:
python3 -m venv .venv
source .venv/bin/activate
```

2) Install dependencies

```bash
pip install -r requirements.txt
# If you need RDKit, install via conda:
# conda install -c conda-forge rdkit
```

3) Run the GUI launcher

```bash
python3 run_goad_v1.py
```

Notes
- RDKit is often not available via pip on macOS — prefer conda for RDKit.
- MatterSim may require additional system dependencies; check its docs.
- If you see GUI-related errors, ensure `tkinter` is installed on your system.

Example quick test (non-GUI):

```bash
python3 -c "import goad_v1; print(goad_v1.__version__)"
```
