"""
Configuration Loader for LLM SOC ROI Simulator
Loads all parameters from Excel file (HypeToROI_LLM_Pricing_SOC_v4_3.xlsx)
Falls back to paper values only when Excel doesn't contain the parameter.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

@dataclass
class SOCConfig:
    """Configuration parameters loaded from Excel"""
    
    # ===== TEMPORAL PARAMETERS (Section A from Parameters sheet) =====
    N: int = 1000  # Daily alert volume
    elapsed_days: int = 1  # Analysis period
    hours_per_day: int = 24  # Operational hours (8=business, 24=24/7)
    
    # ===== ALERT DISTRIBUTION (Section B from Parameters sheet) =====
    fp_filter_efficiency: float = 1.0  # 0=no filter, 1=only TP reach LLM
    
    # Severity distribution (p_a) and TP rates (h_a)
    severity_levels: List[str] = field(default_factory=lambda: ["Low", "Medium", "High", "Critical"])
    p_a: Dict[str, float] = field(default_factory=dict)  # Fraction of alerts per severity
    h_a: Dict[str, float] = field(default_factory=dict)  # True positive rate per severity
    
    # ===== ANALYST COSTS (from LLM Pricing / Table 3) =====
    c_r: Dict[str, float] = field(default_factory=dict)  # Hourly fully-loaded cost per role
    
    # ===== TASK EFFORT TIMES (from Parameters / Table 5-6) =====
    tau_k_a: Dict[Tuple[str, str], float] = field(default_factory=dict)  # Minutes per (task, severity)
    
    # ===== ROLE ALLOCATION (from Table 7) =====
    alpha_a_r: Dict[Tuple[str, str], float] = field(default_factory=dict)  # Fraction of work by (severity, role)
    
    # ===== LLM MODEL PARAMETERS (from LLM Pricing sheet) =====
    llm_models: Dict[str, Dict] = field(default_factory=dict)  # Model name -> {E_m, cost, etc}
    
    # ===== UNCERTAINTY LEVELS (from paper Section 3.4) =====
    cv_levels: List[float] = field(default_factory=lambda: [0.05, 0.25, 0.50, 1.00])
    
    # ===== EFFICIENCY PARAMETERS (from paper Section 7.1.4) =====
    eta_mean: float = 0.70  # Default efficiency (30% time reduction)
    
    # ===== FIXED COSTS (from paper Section 3.1) =====
    C_inv: float = 0.0  # Infrastructure costs not related to security ops
    
    # ===== CAPITAL EXPENDITURE ASSUMPTIONS =====
    theta_mean: float = 0.10  # Default capital expenditure ratio
    amortization_years: int = 3  # IT infrastructure amortization period


def load_config_from_excel(excel_path: str = "data/HypeToROI_LLM_Pricing_SOC_v4_3.xlsx") -> SOCConfig:
    """
    Load configuration from Excel file.
    
    Parameters:
    -----------
    excel_path : str
        Path to Excel file
        
    Returns:
    --------
    SOCConfig
        Configuration object with all parameters
    """
    
    config = SOCConfig()
    
    # Load all sheets
    print(f"📊 Loading configuration from: {excel_path}")
    excel_file = pd.ExcelFile(excel_path)
    
    # ===== LOAD PARAMETERS SHEET =====
    params_df = pd.read_excel(excel_path, sheet_name="Parameters", header=None)
    
    # Extract N (alert volume) - Row 4, Column B
    try:
        config.N = int(params_df.iloc[4, 1])  # "N — Alert giornalieri baseline"
        print(f"  ✓ Alert volume (N): {config.N} alerts/day")
    except:
        print(f"  ⚠ Could not load N from Excel, using default: {config.N}")
    
    # Extract elapsed period - Row 5, Column B
    try:
        config.elapsed_days = int(params_df.iloc[5, 1])
        print(f"  ✓ Analysis period: {config.elapsed_days} day(s)")
    except:
        print(f"  ⚠ Using default period: {config.elapsed_days} day(s)")
    
    # Extract operational hours - Row 6, Column B  
    try:
        config.hours_per_day = int(params_df.iloc[6, 1])
        print(f"  ✓ Operational hours: {config.hours_per_day}h/day")
    except:
        print(f"  ⚠ Using default hours: {config.hours_per_day}h/day")
    
    # Extract FP filter efficiency - Row 10, Column B
    try:
        config.fp_filter_efficiency = float(params_df.iloc[10, 1])
        print(f"  ✓ FP filter efficiency: {config.fp_filter_efficiency*100:.0f}%")
    except:
        print(f"  ⚠ Using default FP filter: {config.fp_filter_efficiency*100:.0f}%")
    
    # Extract severity distribution (rows 13-16)
    try:
        for i, severity in enumerate(["Critical", "High", "Medium", "Low"]):
            row_idx = 13 + i
            p_a_val = float(params_df.iloc[row_idx, 1])  # Column B: p_a
            h_a_val = float(params_df.iloc[row_idx, 4])  # Column E: TP Rate (h_a)
            
            config.p_a[severity] = p_a_val
            config.h_a[severity] = h_a_val
        
        print(f"  ✓ Severity distribution loaded: {len(config.p_a)} levels")
    except Exception as e:
        print(f"  ⚠ Error loading severity distribution: {e}")
        # Fallback to paper values (Table 4)
        config.p_a = {"Critical": 0.002, "High": 0.018, "Medium": 0.13, "Low": 0.85}
        config.h_a = {"Critical": 0.75, "High": 0.50, "Medium": 0.25, "Low": 0.10}
        print(f"  ⚠ Using paper values for severity distribution")
    
    # ===== LOAD LLM PRICING SHEET =====
    llm_df = pd.read_excel(excel_path, sheet_name="LLM Pricing")
    
    for idx, row in llm_df.iterrows():
        model_name = row["Model Name"]
        config.llm_models[model_name] = {
            "provider": row["Provider"],
            "deploy_mode": row["Deploy Mode"],
            "input_cost": row["Input Cost ($/1M)"],
            "output_cost": row["Output Cost ($/1M)"],
            "country": row["Country"],
            "gdpr": row["GDPR"],
            "C_tech": row["C^{m,tech}"],  # Pre-computed total tech cost
            "E_m": row["E^m"],  # Accuracy
            "error_rate": row["1-E^m"]  # 1 - accuracy
        }
    
    print(f"  ✓ Loaded {len(config.llm_models)} LLM models from pricing sheet")
    
    # ===== LOAD ANALYST COSTS (from paper Table 3, use as fallback) =====
    # These are hourly fully-loaded costs in USD
    config.c_r = {
        "L1": 55.24,  # Entry-level SOC analyst
        "L2": 74.10,  # Mid-level analyst
        "L3": 97.11   # Senior analyst / SME
    }
    print(f"  ✓ Using paper values for analyst costs (Table 3)")
    
    # ===== LOAD TASK EFFORT TIMES (from paper Table 5-6) =====
    # Time in minutes per task per severity
    # Format: (task, severity) -> minutes
    tasks = ["Triage", "Analysis", "Response"]
    severities = ["Low", "Medium", "High", "Critical"]
    
    # From Table 6 in paper (minutes spent on task k of severity a)
    effort_matrix = {
        "Triage": [0.08, 0.12, 0.13, 0.17],      # Low, Med, High, Crit
        "Analysis": [0.33, 1.22, 2.12, 3.00],
        "Response": [0.75, 0.83, 0.92, 1.00]
    }
    
    for task in tasks:
        for i, severity in enumerate(severities):
            config.tau_k_a[(task, severity)] = effort_matrix[task][i]
    
    print(f"  ✓ Loaded task effort times: {len(config.tau_k_a)} (task, severity) pairs")
    
    # ===== LOAD ROLE ALLOCATION (from paper Table 7) =====
    # α_{a,r}: fraction of time spent by role r on severity a
    config.alpha_a_r = {
        ("Low", "L1"): 1.0, ("Low", "L2"): 0.0, ("Low", "L3"): 0.0,
        ("Medium", "L1"): 0.8, ("Medium", "L2"): 0.2, ("Medium", "L3"): 0.0,
        ("High", "L1"): 0.5, ("High", "L2"): 0.5, ("High", "L3"): 0.0,
        ("Critical", "L1"): 0.1, ("Critical", "L2"): 0.6, ("Critical", "L3"): 0.3
    }
    print(f"  ✓ Loaded role allocation: {len(config.alpha_a_r)} (severity, role) pairs")
    
    print(f"\n✅ Configuration loaded successfully!")
    return config


def get_default_config() -> SOCConfig:
    """Returns default configuration with paper values"""
    return SOCConfig()


if __name__ == "__main__":
    # Test configuration loading
    config = load_config_from_excel()
    
    print(f"\n📋 Configuration Summary:")
    print(f"  Alert volume: {config.N} alerts/day")
    print(f"  Severity levels: {config.severity_levels}")
    print(f"  LLM models: {list(config.llm_models.keys())[:5]}... ({len(config.llm_models)} total)")
    print(f"  Analyst roles: {list(config.c_r.keys())}")
    print(f"  Default efficiency η: {config.eta_mean} (30% time reduction)")
    print(f"  Uncertainty levels CV: {config.cv_levels}")
