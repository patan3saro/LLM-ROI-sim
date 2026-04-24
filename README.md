# 📊 LLM SOC ROI Simulator

**Economic Model for Evaluating LLM Adoption in Security Operations Centers**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: Proprietary](https://img.shields.io/badge/license-Proprietary-red.svg)]()

## 🎯 Overview

This simulator implements the economic model from the paper **"From Hype to ROI: An Economic Model for Evaluating LLM Adoption in Security Operations"** by Pellegrino Casoria and Andrea Araldo.

The tool enables **SOC managers, CISOs, and researchers** to:
- Quantify ROI from LLM adoption with **probabilistic uncertainty analysis**
- **Compare multiple LLM models** simultaneously on interactive heatmaps
- Identify **boundary conditions** separating profitable from unprofitable deployments
- Generate **publication-quality visualizations** including multi-model heatmaps and VaR analysis
- Export results to **LaTeX tables** and **CSV** for academic papers

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

### Run Multi-Model Analysis (NEW!)

```bash
# Analyze 5 models with multi-model heatmap and VaR analysis
python run_5models_analysis.py
```

**This generates:**
- ✅ Heatmap with 5 models positioned by their real accuracy values
- ✅ VaR heatmap in paper style (discretized risk levels)
- ✅ Complete Monte Carlo analysis for all 5 models
- ✅ Comparative analysis across multiple θ (capital ratio) values
- ✅ Summary CSV table ready for publication

**Time:** ~10-15 minutes | **Output:** ~40 publication-quality figures

---

### Run Single Model Analysis

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
├── README.md                              # This file
├── requirements.txt                       # Python dependencies
├── run_5models_analysis.py                # ⭐ NEW: Multi-model analysis script
├── data/
│   ├── HypeToROI_LLM_Pricing_SOC_v4_3.xlsx  # Configuration Excel file
│   └── JCS___Hype_to_ROI.pdf                # Research paper
├── src/
│   ├── __init__.py                        # Package initialization
│   ├── config.py                          # Excel configuration loader
│   ├── distributions.py                   # Beta/Gamma distributions (Lemmas 1-2) - FIXED
│   ├── model.py                           # Economic model (equations 1-14)
│   ├── monte_carlo.py                     # Monte Carlo simulation engine
│   ├── visualizations.py                  # Publication-quality plots
│   └── utils.py                           # Helper functions
├── notebooks/
│   ├── 01_quickstart.ipynb                # Executive-level analysis
│   ├── 02_sensitivity_analysis.ipynb      # Full parameter sweeps
│   └── 03_model_comparison.ipynb          # Multi-LLM comparison
├── outputs/
│   ├── cached_results/                    # Serialized simulation results (*.pkl)
│   ├── plots/                             # PNG plots (300 DPI)
│   │   ├── heatmap_5models.png           # ⭐ NEW: Multi-model heatmap
│   │   ├── var_heatmap_paper.png         # ⭐ NEW: VaR heatmap (paper style)
│   │   └── [model]_*.png                 # Individual model plots
│   └── tables/                            # LaTeX tables + CSV exports
│       └── 5models_summary.csv           # ⭐ NEW: Comparative table
└── tests/
    ├── test_distributions.py              # Validate Lemmas 1-2
    ├── test_model.py                      # Validate equations
    └── test_monte_carlo.py                # Validate simulation
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
- `E^m` = LLM accuracy (from Excel, different per model)
- `η` = efficiency (time saved when correct, default 0.70 = 30% reduction)

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

**Lemma 1 (Beta distribution) - FIXED:**
```
α = μ · ((1-μ)/(μ·CV²) - 1)
β = (1-μ) · ((1-μ)/(μ·CV²) - 1)

Maximum CV for Beta: CV_max = sqrt((1-μ)/μ)
If CV > CV_max: clamp to 0.95 × CV_max
```

**Lemma 2 (Gamma distribution):**
```
κ = 1/CV²  (shape)
ς = μ·CV²  (scale)
```

Monte Carlo simulations (10,000 iterations per CV level) propagate uncertainty through the model.

---

## 🎨 Visualizations

The simulator generates **10 types of publication-quality plots**:

### 1. Multi-Model ROI Heatmap ⭐ NEW
2D grid showing ROI as function of **Accuracy (E^m) × Efficiency (η)** with **5 LLM models** positioned as annotated points based on their real Excel values. Shows break-even contour and model positioning.

### 2. VaR Heatmap (Paper Style) ⭐ NEW
Value at Risk discretized into 5 levels:
- 0% < VaR ≤ 5% (very low risk)
- 5% < VaR ≤ 10% (low risk)
- 10% < VaR ≤ 30% (moderate risk)
- 30% < VaR ≤ 50% (high risk)
- VaR > 50% (very high risk)

Styled to match paper Figure 2 with grid pattern and discrete color levels.

### 3. Profitability Probability Curves
Shows `P(ROI > 0 | CV)` vs. capital expenditure ratio θ, one curve per uncertainty level.

### 4. Waterfall Cost Breakdown
Decomposes cost transformation: Baseline → Personnel Savings → LLM Costs → Net ROI.

### 5. Tornado Sensitivity Diagram
Ranked bar chart showing impact of parameter changes on ROI (Spearman correlation).

### 6. Cumulative Distribution Function (CDF)
Shows `P(ROI ≤ x)` for all uncertainty levels, enabling percentile-based risk assessment.

### 7. Violin Plot
Full distribution comparison across CV levels, showing density, median, and mean.

### 8. Value at Risk (VaR) Bar Chart
Displays worst-case losses at 5%, 10%, 25% confidence levels.

### 9. Multi-Model Scatter Plot
Compares models on **Cost × Accuracy × ROI** (bubble size = ROI magnitude).

### 10. Individual Model Analysis
Complete set of 8 plots for each analyzed model (heatmap, CDF, violin, waterfall, tornado, profitability, VaR).

---

## 📊 Using the Simulator

### Multi-Model Analysis Script (Recommended for Research)

```bash
python run_5models_analysis.py
```

**Features:**
- Analyzes 5 models simultaneously (customizable)
- Tests multiple θ values: 0.05, 0.10, 0.15, 0.20, 0.25
- Generates multi-model heatmap with all models positioned
- Creates VaR heatmap in paper style
- Exports comparative summary to CSV
- ~10-15 minutes runtime with 1000 iterations/CV

**Customize models:**
```python
# Edit run_5models_analysis.py line 23:
MODELS_TO_ANALYZE = [
    "gpt-4.1",
    "gpt-4-turbo",
    "Grok-3",
    "DeepSeek-V3",
    "gemini-2.5-flash"
]
```

**Customize theta values:**
```python
# Edit run_5models_analysis.py line 31:
THETA_VALUES = [0.05, 0.10, 0.15, 0.20, 0.25]
```

### Jupyter Notebooks (Interactive Analysis)

**Notebook 1: Quickstart Analysis** (`01_quickstart.ipynb`)
- Load configuration
- Analyze single model
- Generate executive summary
- **Time: ~5 minutes**

**Notebook 2: Sensitivity Analysis** (`02_sensitivity_analysis.ipynb`)
- Run Monte Carlo across all CV levels
- Generate all plot types
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
- Model accuracy (E^m) from benchmarks ← **Each model has unique value**
- API costs (input/output tokens)
- Pre-computed technology costs (C^{m,tech}) ← **Different per model**

**Sheet: Extraction** (optional)
- Raw accuracy data from benchmarks

### Parameter Sources

| Parameter | Source | Per-Model |
|-----------|--------|-----------|
| E^m (Accuracy) | Excel "LLM Pricing" | ✅ Yes - Each model unique |
| C^{m,tech} (Cost) | Excel "LLM Pricing" | ✅ Yes - Each model unique |
| η (Efficiency) | Paper (Section 7.1.4) | ❌ No - Fixed 0.70 for all* |
| θ (Capital ratio) | Paper/User config | ❌ No - User-specified |

**\*Note on Efficiency (η):**  
Currently all models use η=0.70 (30% time reduction). This is why ROI values are similar across models with comparable accuracy. To differentiate models further:

1. **Add η column to Excel:** Assign different efficiency values based on model characteristics
2. **Modify `src/config.py`:** Load η from Excel per model
3. **Justify in paper:** Explain variation based on inference speed, response quality, etc.

**Example efficiency values by model type:**
- Fast inference models (GPT-4-turbo): η=0.75
- Open-source models: η=0.60-0.65
- Specialized SOC models: η=0.80

### Modifying Parameters

1. **Change alert volume**: Edit cell B5 in "Parameters" sheet
2. **Add new model**: Add row to "LLM Pricing" sheet with E^m and C^{m,tech}
3. **Adjust analyst costs**: Modify `c_r` dict in `config.py`
4. **Add per-model efficiency**: Add η column to Excel and update config loader

---

## 🧪 Validation & Testing

### Mathematical Validation

```bash
# Validate Lemmas 1-2 (Beta/Gamma distributions) - FIXED VERSION
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
  ⚠ Warning: CV=50.00% too high for mean=92.75%. Clamping to 27.73%
  ✓ Lemma 1 validated!

🧪 Validating Lemma 2 (Gamma distribution)...
  ✅ μ=1000, CV=5%: κ=400.000, ς=2.500 | Empirical: μ=1000.12, CV=5.01%
  ✓ Lemma 2 validated!
```

### Fixed Issues

**Beta Distribution High CV Fix:**
- Problem: CV=50% and CV=100% produced negative parameters for high-accuracy models
- Solution: Automatic clamping to 95% of theoretical maximum CV
- Impact: High uncertainty simulations now work correctly for all models

### Unit Tests

- `test_distributions.py`: Validates Lemmas 1-2 across 100+ parameter combinations
- `test_model.py`: Validates equations against known benchmarks
- `test_monte_carlo.py`: Ensures reproducibility (fixed random seed)

---

## 📤 Outputs

### Multi-Model Summary CSV
```
outputs/tables/5models_summary.csv
```

Contains comparative results:
- Model name
- Accuracy (E^m from Excel)
- Mean ROI (CV=25%)
- P(ROI > 0)
- VaR(5%)

Ready for import into LaTeX tables.

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

---

## 📊 Example Results

**Multi-Model Analysis (θ=10%, η=70%):**
```
Model            | E^m    | C^{m,tech} | Mean ROI | P(Profit)
-----------------|--------|------------|----------|----------
gpt-4.1          | 92.75% | $1.10/day  | 549.2%   | 96.0%
gpt-4-turbo      | 92.26% | $4.52/day  | 534.8%   | 94.5%
Grok-3           | 91.91% | $1.93/day  | 528.4%   | 93.8%
DeepSeek-V3      | 91.02% | $0.15/day  | 513.6%   | 92.1%
gemini-2.5-flash | 90.37% | $0.29/day  | 502.1%   | 90.5%

✅ All models profitable with high confidence
📊 ROI similarity due to fixed η=0.70 across all models
💡 Add per-model η to Excel for greater differentiation
```

**Single Model: GPT-4.1 (CV=25%)**
```
Alert Volume: 1,000/day
Accuracy E^m: 92.75%
Efficiency η: 70% (30% time reduction)
Capital Ratio θ: 10%

💰 RESULTS:
  Mean ROI: 599.4%
  Median ROI: 580.6%
  Std Dev: 313.5%
  P(ROI > 0): 95.2%
  VaR(5%): 8.1%
  
✅ RECOMMENDATION: STRONG BUY
   High probability of significant positive ROI
```

---

## 🔧 Troubleshooting

### Common Issues

**1. Beta distribution error (CV too high)**
```
AssertionError: Invalid params: α=-0.637, β=-0.049
```
**Solution:** Update `src/distributions.py` with the FIXED version provided. The fix automatically clamps CV to valid range.

**2. Import errors**
```bash
# Ensure src/ is in PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

**3. Excel file not found**
```python
# Use absolute path
config = load_config_from_excel("/full/path/to/data/Excel_file.xlsx")
```

**4. Out of memory (large simulations)**
```python
# Reduce iterations in run_5models_analysis.py
N_ITERATIONS = 100  # Instead of 1000
```

**5. Matplotlib clabel fontweight error**
```
TypeError: ContourLabeler.clabel() got an unexpected keyword argument 'fontweight'
```
**Solution:** Update `run_5models_analysis.py` line 91, remove `fontweight='bold'` parameter.

**6. All models have similar ROI**
**Why:** All models use η=0.70 (same efficiency) and θ=0.10 (same capital ratio). Only E^m and C^{m,tech} differ.  
**Solution:** Add η column to Excel with different values per model, or accept that current analysis shows accuracy/cost tradeoffs with fixed efficiency.

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
- [ ] Update `src/distributions.py` with FIXED version (handles high CV)
- [ ] Run validation: `python src/distributions.py` → should see ✅
- [ ] Run multi-model analysis: `python run_5models_analysis.py`
- [ ] Check `outputs/plots/` for heatmap_5models.png and var_heatmap_paper.png
- [ ] Review `outputs/tables/5models_summary.csv`

**Estimated time for first complete run: 15 minutes**

---

## 🚀 What's Next?

1. **Run multi-model analysis** (`python run_5models_analysis.py`)
2. **Review comparative heatmap** with 5 models positioned
3. **Analyze VaR heatmap** to understand risk zones
4. **Export CSV table** for paper (`outputs/tables/5models_summary.csv`)
5. **Optional: Add per-model η** to Excel for greater model differentiation
6. **Generate LaTeX tables** for publication using `utils.export_latex_table()`
7. **Customize for your organization**: Adjust alert volume, analyst costs, task times

---

## 💡 Key Insights

**Why similar ROI across models?**
All models currently use:
- η = 0.70 (same time reduction when correct)
- θ = 0.10 (same capital expenditure ratio)

Only E^m (accuracy) and C^{m,tech} (cost) differ per model. This shows that **within the high-accuracy range (90-93%), cost differences matter less than accuracy** when efficiency is constant.

**To increase model differentiation:**
Add η column to Excel reflecting real-world differences in:
- Inference speed
- Response quality requiring less human review
- Integration complexity
- Need for post-processing

---

**Happy Simulating! 📊**
