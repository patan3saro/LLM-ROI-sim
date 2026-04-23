# 📊 LLM SOC ROI Simulator

**Economic Model for Evaluating LLM Adoption in Security Operations Centers**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: Proprietary](https://img.shields.io/badge/license-Proprietary-red.svg)]()

## 🎯 Overview

This simulator implements the economic model from the paper **"From Hype to ROI: An Economic Model for Evaluating LLM Adoption in Security Operations"** by Pellegrino Casoria and Andrea Araldo.

The tool enables **SOC managers, CISOs, and researchers** to:
- Quantify ROI from LLM adoption with **probabilistic uncertainty analysis**
- Compare multiple LLM models across accuracy, cost, and efficiency dimensions
- Identify **boundary conditions** separating profitable from unprofitable deployments
- Generate **publication-quality visualizations** and **executive summaries**

---

## 🚀 Quick Start

### Installation

```bash
# Clone or extract the project
cd llm-soc-roi-simulator

# Install dependencies
pip install -r requirements.txt

# Verify installation
python src/config.py
```

### Run Your First Analysis

```python
import sys
sys.path.insert(0, 'src')

from config import load_config_from_excel
from model import SOCEconomicModel

# Load configuration from Excel
config = load_config_from_excel()

# Initialize model
model = SOCEconomicModel(config)

# Analyze GPT-4.1
result = model.analyze(
    model_name="gpt-4.1",
    E_m=0.9275,  # 92.75% accuracy from Excel
    eta=0.70,     # 30% time reduction
    theta=0.10    # 10% capital expenditure ratio
)

print(f"ROI: {result.roi:.2%}")
print(f"Operational Savings: ${result.delta_C:,.2f}/day")
```

---

## 📁 Project Structure

```
llm-soc-roi-simulator/
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── data/
│   ├── HypeToROI_LLM_Pricing_SOC_v4_3.xlsx  # Configuration Excel file
│   └── JCS___Hype_to_ROI.pdf                # Research paper
├── src/
│   ├── __init__.py              # Package initialization
│   ├── config.py                # Excel configuration loader
│   ├── distributions.py         # Beta/Gamma distributions (Lemmas 1-2)
│   ├── model.py                 # Economic model (equations 1-14)
│   ├── monte_carlo.py           # Monte Carlo simulation engine
│   ├── visualizations.py        # Publication-quality plots
│   └── utils.py                 # Helper functions
├── notebooks/
│   ├── 01_quickstart.ipynb      # Executive-level analysis
│   ├── 02_sensitivity_analysis.ipynb  # Full parameter sweeps
│   └── 03_model_comparison.ipynb      # Multi-LLM comparison
├── outputs/
│   ├── cached_results/          # Serialized simulation results (*.pkl)
│   ├── plots/                   # PNG plots
│   ├── tables/                  # LaTeX tables
│   └── executive_summary.pdf    # Auto-generated report
└── tests/
    ├── test_distributions.py    # Validate Lemmas 1-2
    ├── test_model.py             # Validate equations
    └── test_monte_carlo.py       # Validate simulation
```

---

## 📐 Mathematical Model

The simulator implements equations (1)-(14) from the paper:

### Core Equations

**Cost without LLM (Equation 2):**
```
C^{noLLM} = Σ_{r∈R} c_r · τ^{noLLM}_r + C_inv
```

**Cost with LLM (Equation 7):**
```
C^m = Σ_{r∈R} c_r · τ^m_r + C^{m,tech} + C_inv
```

**Time with LLM (Equation 6):**
```
τ^m_r = N · Σ_{a∈A} h_a · p_a · Σ_{k∈K} τ_{k,r,a} · [1 - E^m · η]
```
where:
- `E^m` = LLM accuracy (from Excel)
- `η` = efficiency (time saved, default 0.70 = 30% reduction)

**ROI (Equation 13):**
```
ROI^m = (ΔC^m - C_cap) / C_cap
```

**Profitability Condition (Equation 14):**
```
ROI^m > y ⟺ θ < ΔC^m / ((1+y)·C^{noLLM})
```

### Uncertainty Quantification (Section 3.4)

Parameters are modeled as **random variables**:

- **Efficiency η**: `Beta(α, β)` with mean 0.70, CV ∈ {5%, 25%, 50%, 100%}
- **Capital ratio θ**: `Beta(α, β)` with mean 0.10, CV levels
- **Accuracy E^m**: `Beta(α, β)` centered on Excel values

**Lemma 1 (Beta distribution):**
```
α = μ · ((1-μ)/(μ·CV²) - 1)
β = (1-μ) · ((1-μ)/(μ·CV²) - 1)
```

**Lemma 2 (Gamma distribution):**
```
κ = 1/CV²  (shape)
ς = μ·CV²  (scale)
```

Monte Carlo simulations (10,000 iterations per CV level) propagate uncertainty through the model.

---

## 🎨 Visualizations

The simulator generates **8 types of publication-quality plots**:

### 1. ROI Heatmap
2D grid showing ROI as a function of **Accuracy (E^m) × Efficiency (η)** with break-even contours.

### 2. Profitability Probability Curves
Shows `P(ROI > 0 | CV)` vs. capital expenditure ratio θ, one curve per uncertainty level.

### 3. Waterfall Cost Breakdown
Decomposes cost transformation: Baseline → Personnel Savings → LLM Costs → Net ROI.

### 4. Tornado Sensitivity Diagram
Ranked bar chart showing impact of parameter changes on ROI (Spearman correlation).

### 5. Cumulative Distribution Function (CDF)
Shows `P(ROI ≤ x)` for all uncertainty levels, enabling percentile-based risk assessment.

### 6. Violin Plot
Full distribution comparison across CV levels, showing density, median, and mean.

### 7. Value at Risk (VaR) Chart
Displays worst-case losses at 5%, 10%, 25% confidence levels.

### 8. Multi-Model Scatter Plot
Compares models on **Cost × Accuracy × ROI** (bubble size = ROI magnitude).

---

## 📊 Using the Simulator

### Jupyter Notebooks (Recommended)

**Notebook 1: Quickstart Analysis** (`01_quickstart.ipynb`)
- Load configuration
- Analyze single model
- Generate executive summary
- **Time: ~5 minutes**

**Notebook 2: Sensitivity Analysis** (`02_sensitivity_analysis.ipynb`)
- Run Monte Carlo across all CV levels
- Generate all 8 plot types
- Export LaTeX tables
- **Time: ~20 minutes (10K iterations)**

**Notebook 3: Model Comparison** (`03_model_comparison.ipynb`)
- Compare top 10 models
- Generate ranking tables
- Interactive parameter exploration
- **Time: ~60 minutes**

### Python API

```python
from monte_carlo import MonteCarloSimulator
from visualizations import ROIVisualizer

# Create simulator
config = load_config_from_excel()
simulator = MonteCarloSimulator(config, n_iterations=10000)

# Run simulation
results = simulator.run_all_cv_levels("gpt-4.1")

# Generate plots
visualizer = ROIVisualizer()
visualizer.generate_all_plots(results, breakdown, "gpt-4.1")

# Save results
simulator.save_results(results, "gpt4_results.pkl")
```

---

## 📋 Configuration

### Excel File Structure

The simulator reads **all parameters** from `data/HypeToROI_LLM_Pricing_SOC_v4_3.xlsx`:

**Sheet: Parameters**
- Alert volume (N): 1000 alerts/day
- Severity distribution (p_a, h_a)
- FP filter efficiency

**Sheet: LLM Pricing**
- Model accuracy (E^m) from benchmarks
- API costs (input/output tokens)
- Pre-computed technology costs (C^{m,tech})

**Sheet: Extraction** (optional)
- Raw accuracy data from benchmarks

### Modifying Parameters

1. **Change alert volume**: Edit cell B5 in "Parameters" sheet
2. **Add new model**: Add row to "LLM Pricing" sheet with required columns
3. **Adjust analyst costs**: Modify `c_r` dict in `config.py`

---

## 🧪 Validation & Testing

### Mathematical Validation

```bash
# Validate Lemmas 1-2 (Beta/Gamma distributions)
python src/distributions.py

# Validate economic model (equations 1-14)
python src/model.py

# Run all tests
pytest tests/
```

**Expected Output:**
```
🧪 Validating Lemma 1 (Beta distribution)...
  ✅ μ=0.70, CV=5%: α=29.167, β=12.500 | Empirical: μ=0.7001, CV=5.02%
  ✓ Lemma 1 validated!

🧪 Validating Lemma 2 (Gamma distribution)...
  ✅ μ=1000, CV=5%: κ=400.000, ς=2.500 | Empirical: μ=1000.12, CV=5.01%
  ✓ Lemma 2 validated!
```

### Unit Tests

- `test_distributions.py`: Validates Lemmas 1-2 across 100+ parameter combinations
- `test_model.py`: Validates equations against known benchmarks
- `test_monte_carlo.py`: Ensures reproducibility (fixed random seed)

---

## 📤 Outputs

### Cached Results
```python
# Save simulation results (avoids re-running)
simulator.save_results(results, "model_results.pkl")

# Load later
loaded_results = simulator.load_results("model_results.pkl")
```

### LaTeX Tables
```python
from utils import export_latex_table

# Export summary table
summary_df = pd.DataFrame(summary_data)
export_latex_table(summary_df, 
                  filename="roi_summary.tex",
                  caption="ROI Summary Across Models",
                  label="tab:roi_summary")
```

### Executive Summary (PDF)
Auto-generated 1-page report with:
- Key metrics (mean ROI, P(profit), VaR)
- Investment recommendation
- Top 3 models ranked
- Risk assessment

---

## 📊 Example Results

**Model: GPT-4.1**
```
Alert Volume: 1,000/day
Accuracy E^m: 92.75%
Efficiency η: 70% (30% time reduction)
Capital Ratio θ: 10%

💰 RESULTS (CV=25%):
  Mean ROI: 42.3%
  P(ROI > 0): 94.2%
  VaR(5%): 8.1%
  
✅ RECOMMENDATION: STRONG BUY
   High probability of significant positive ROI
```

---

## 🔧 Troubleshooting

### Common Issues

**1. Import errors**
```bash
# Ensure src/ is in PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

**2. Excel file not found**
```python
# Use absolute path
config = load_config_from_excel("/full/path/to/data/Excel_file.xlsx")
```

**3. Out of memory (large simulations)**
```python
# Reduce iterations
simulator = MonteCarloSimulator(config, n_iterations=1000)
```

**4. Plots not saving**
```bash
# Create output directories manually
mkdir -p outputs/plots outputs/cached_results outputs/tables
```

---

## 📚 References

1. **Paper**: "From Hype to ROI: An Economic Model for Evaluating LLM Adoption in Security Operations" (2026)
   - Authors: Pellegrino Casoria, Andrea Araldo
   - Institutions: University of Naples Federico II, Télécom SudParis

2. **Benchmarks**:
   - CyberSOCEval (Meta)
   - SecBench (multilingual security knowledge)
   - CTIBench (threat intelligence)
   - CyberMetric (NIST/RFC standards)
   - DFIR-Metric (forensics)

3. **Frameworks**:
   - NIST Cybersecurity Framework 2.0
   - FIRST CSIRT Services Framework v2.1
   - SOC-CMM (Capability Maturity Model)

---

## 🤝 Contributing

This is a research prototype. For questions or collaboration:
- **Pellegrino Casoria**: pellegrino.casoria@unina.it
- **Andrea Araldo**: andrea.araldo@telecom-sudparis.eu

---

## 📄 License

Proprietary - Research Use Only

---

## 🎓 Citation

```bibtex
@article{casoria2026hype,
  title={From Hype to ROI: An Economic Model for Evaluating LLM Adoption in Security Operations},
  author={Casoria, Pellegrino and Araldo, Andrea},
  journal={Conference Proceedings},
  year={2026}
}
```

---

## ✅ Checklist for First Run

- [ ] Install dependencies (`pip install -r requirements.txt`)
- [ ] Verify Excel file exists (`data/HypeToROI_LLM_Pricing_SOC_v4_3.xlsx`)
- [ ] Run validation tests (`python src/distributions.py`, `python src/model.py`)
- [ ] Open `notebooks/01_quickstart.ipynb` in Jupyter
- [ ] Execute all cells
- [ ] Check `outputs/plots/` for generated plots
- [ ] Review executive summary

**Estimated time for first complete run: 30 minutes**

---

## 🚀 What's Next?

1. **Run baseline analysis** (Notebook 01)
2. **Perform full Monte Carlo** (Notebook 02) with 10K iterations
3. **Compare top models** (Notebook 03)
4. **Export LaTeX tables** for paper
5. **Generate executive summary** for stakeholders
6. **Customize parameters** for your organization's specific context

---

**Happy Simulating! 📊**
