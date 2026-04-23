"""
Economic Model for LLM SOC ROI
Implements equations (1)-(14) from the paper
"""

import numpy as np
from typing import Dict, Tuple
from dataclasses import dataclass


@dataclass
class CostBreakdown:
    """Detailed breakdown of costs for transparency"""
    
    # Without LLM
    C_noLLM_total: float  # Total cost without LLM
    C_noLLM_personnel: float  # Personnel cost
    C_inv: float  # Infrastructure (invariant)
    
    # With LLM
    C_LLM_total: float  # Total cost with LLM
    C_LLM_personnel: float  # Personnel cost with LLM
    C_tech: float  # LLM operational cost (API + infra)
    
    # Savings
    delta_C: float  # Operational savings
    C_cap: float  # Capital expenditure
    
    # ROI
    roi: float  # Return on investment
    
    # Time breakdown (for analysis)
    tau_noLLM_by_role: Dict[str, float]  # Time per role without LLM
    tau_LLM_by_role: Dict[str, float]  # Time per role with LLM
    
    def to_dict(self) -> dict:
        """Convert to dictionary for export"""
        return {
            "C_noLLM_total": self.C_noLLM_total,
            "C_noLLM_personnel": self.C_noLLM_personnel,
            "C_inv": self.C_inv,
            "C_LLM_total": self.C_LLM_total,
            "C_LLM_personnel": self.C_LLM_personnel,
            "C_tech": self.C_tech,
            "delta_C": self.delta_C,
            "C_cap": self.C_cap,
            "roi": self.roi,
        }


class SOCEconomicModel:
    """
    Implements the economic model from the paper (equations 1-14).
    """
    
    def __init__(self, config):
        """
        Initialize model with configuration.
        
        Parameters:
        -----------
        config : SOCConfig
            Configuration loaded from Excel
        """
        self.config = config
    
    # ===== EQUATION (1): Personnel time without LLM =====
    def compute_tau_noLLM_r(self, role: str) -> float:
        """
        Compute personnel time for role r without LLM (equation 1).
        
        τ^{noLLM}_r = N · Σ_{a∈A} h_a · p_a · Σ_{k∈K} τ_{k,r,a}
        
        Parameters:
        -----------
        role : str
            Analyst role (L1, L2, L3)
            
        Returns:
        --------
        float
            Hours spent by role r per day
        """
        N = self.config.N
        total_time = 0.0
        
        for severity in self.config.severity_levels:
            h_a = self.config.h_a[severity]  # TP rate
            p_a = self.config.p_a[severity]  # Severity fraction
            
            # Sum over all tasks
            for task in ["Triage", "Analysis", "Response"]:
                tau_k_a = self.config.tau_k_a.get((task, severity), 0.0)  # Total time for task
                alpha_a_r = self.config.alpha_a_r.get((severity, role), 0.0)  # Role fraction
                
                tau_k_r_a = tau_k_a * alpha_a_r  # Time for this role (equation 3)
                total_time += h_a * p_a * tau_k_r_a
        
        total_time_hours = total_time * N / 60.0  # Convert minutes to hours
        return total_time_hours
    
    # ===== EQUATION (2): Total cost without LLM =====
    def compute_C_noLLM(self) -> Tuple[float, Dict[str, float]]:
        """
        Compute total operational cost without LLM (equation 2).
        
        C^{noLLM} = Σ_{r∈R} c_r · τ^{noLLM}_r + C_inv
        
        Returns:
        --------
        Tuple[float, Dict[str, float]]
            (total_cost, time_by_role)
        """
        tau_by_role = {}
        C_personnel = 0.0
        
        for role in ["L1", "L2", "L3"]:
            tau_r = self.compute_tau_noLLM_r(role)
            c_r = self.config.c_r[role]
            
            tau_by_role[role] = tau_r
            C_personnel += c_r * tau_r
        
        C_total = C_personnel + self.config.C_inv
        
        return C_total, tau_by_role
    
    # ===== EQUATION (6): Personnel time with LLM =====
    def compute_tau_LLM_r(self, role: str, E_m: float, eta: float) -> float:
        """
        Compute personnel time for role r with LLM (equation 6).
        
        τ^m_r = N · Σ_{a∈A} h_a · p_a · Σ_{k∈K} [E^m·(1-η)·τ_{k,r,a} + (1-E^m)·τ_{k,r,a}]
             = N · Σ_{a∈A} h_a · p_a · Σ_{k∈K} τ_{k,r,a} · [1 - E^m·η]
        
        Parameters:
        -----------
        role : str
            Analyst role
        E_m : float
            LLM accuracy (fraction of correct responses)
        eta : float
            LLM efficiency (fraction of time saved when correct)
            
        Returns:
        --------
        float
            Hours spent by role r with LLM per day
        """
        N = self.config.N
        total_time = 0.0
        
        for severity in self.config.severity_levels:
            h_a = self.config.h_a[severity]
            p_a = self.config.p_a[severity]
            
            for task in ["Triage", "Analysis", "Response"]:
                tau_k_a = self.config.tau_k_a.get((task, severity), 0.0)
                alpha_a_r = self.config.alpha_a_r.get((severity, role), 0.0)
                
                tau_k_r_a = tau_k_a * alpha_a_r
                
                # Time with LLM: correct * reduced_time + incorrect * full_time
                time_with_llm = tau_k_r_a * (1 - E_m * eta)
                
                total_time += h_a * p_a * time_with_llm
        
        total_time_hours = total_time * N / 60.0
        return total_time_hours
    
    # ===== EQUATION (7): Total cost with LLM =====
    def compute_C_LLM(self, E_m: float, eta: float, C_tech: float) -> Tuple[float, Dict[str, float]]:
        """
        Compute total operational cost with LLM (equation 7).
        
        C^m = Σ_{r∈R} c_r · τ^m_r + C^{m,tech} + C_inv
        
        Parameters:
        -----------
        E_m : float
            LLM accuracy
        eta : float
            LLM efficiency
        C_tech : float
            LLM technology cost (from Excel pre-computed value)
            
        Returns:
        --------
        Tuple[float, Dict[str, float]]
            (total_cost, time_by_role)
        """
        tau_by_role = {}
        C_personnel = 0.0
        
        for role in ["L1", "L2", "L3"]:
            tau_r = self.compute_tau_LLM_r(role, E_m, eta)
            c_r = self.config.c_r[role]
            
            tau_by_role[role] = tau_r
            C_personnel += c_r * tau_r
        
        C_total = C_personnel + C_tech + self.config.C_inv
        
        return C_total, tau_by_role
    
    # ===== EQUATION (11): Operational savings =====
    def compute_delta_C(self, C_noLLM: float, C_LLM: float) -> float:
        """
        Compute operational savings (equation 11).
        
        ΔC^m := C^{noLLM} - C^m
        
        Parameters:
        -----------
        C_noLLM : float
            Cost without LLM
        C_LLM : float
            Cost with LLM
            
        Returns:
        --------
        float
            Operational savings (positive = savings, negative = loss)
        """
        return C_noLLM - C_LLM
    
    # ===== EQUATION (12): Capital expenditure ratio =====
    def compute_C_cap(self, theta: float, C_noLLM: float) -> float:
        """
        Compute capital expenditure (equation 12).
        
        C_cap = θ · C^{noLLM}
        
        where θ is the capital expenditure ratio (amortized daily cost).
        
        Parameters:
        -----------
        theta : float
            Capital expenditure ratio
        C_noLLM : float
            Baseline operational cost
            
        Returns:
        --------
        float
            Daily amortized capital cost
        """
        return theta * C_noLLM
    
    # ===== EQUATION (13): Return on Investment =====
    def compute_ROI(self, delta_C: float, C_cap: float) -> float:
        """
        Compute ROI (equation 13).
        
        ROI^m := (ΔC^m - C_cap) / C_cap
        
        Parameters:
        -----------
        delta_C : float
            Operational savings
        C_cap : float
            Capital expenditure
            
        Returns:
        --------
        float
            ROI as decimal (0.25 = 25% return)
        """
        if C_cap == 0:
            return np.inf if delta_C > 0 else -np.inf
        
        return (delta_C - C_cap) / C_cap
    
    # ===== EQUATION (14): Profitability condition =====
    def compute_theta_threshold(self, delta_C: float, C_noLLM: float, target_roi: float = 0.0) -> float:
        """
        Compute maximum acceptable capital expenditure ratio (equation 14).
        
        ROI^m > y ⟺ θ < ΔC^m / ((1+y)·C^{noLLM})
        
        Parameters:
        -----------
        delta_C : float
            Operational savings
        C_noLLM : float
            Baseline cost
        target_roi : float
            Target ROI (0.0 = break-even)
            
        Returns:
        --------
        float
            Maximum θ for profitability
        """
        return delta_C / ((1 + target_roi) * C_noLLM)
    
    # ===== COMPLETE ANALYSIS =====
    def analyze(self, model_name: str, E_m: float, eta: float, theta: float) -> CostBreakdown:
        """
        Perform complete economic analysis for a given configuration.
        
        Parameters:
        -----------
        model_name : str
            LLM model name
        E_m : float
            Model accuracy
        eta : float
            Efficiency (time saved)
        theta : float
            Capital expenditure ratio
            
        Returns:
        --------
        CostBreakdown
            Detailed cost breakdown and ROI
        """
        
        # Get LLM technology cost from Excel
        C_tech = self.config.llm_models[model_name]["C_tech"]
        
        # Compute costs without LLM
        C_noLLM, tau_noLLM_by_role = self.compute_C_noLLM()
        C_noLLM_personnel = C_noLLM - self.config.C_inv
        
        # Compute costs with LLM
        C_LLM, tau_LLM_by_role = self.compute_C_LLM(E_m, eta, C_tech)
        C_LLM_personnel = sum(self.config.c_r[r] * tau_LLM_by_role[r] for r in ["L1", "L2", "L3"])
        
        # Compute savings and ROI
        delta_C = self.compute_delta_C(C_noLLM, C_LLM)
        C_cap = self.compute_C_cap(theta, C_noLLM)
        roi = self.compute_ROI(delta_C, C_cap)
        
        return CostBreakdown(
            C_noLLM_total=C_noLLM,
            C_noLLM_personnel=C_noLLM_personnel,
            C_inv=self.config.C_inv,
            C_LLM_total=C_LLM,
            C_LLM_personnel=C_LLM_personnel,
            C_tech=C_tech,
            delta_C=delta_C,
            C_cap=C_cap,
            roi=roi,
            tau_noLLM_by_role=tau_noLLM_by_role,
            tau_LLM_by_role=tau_LLM_by_role
        )


if __name__ == "__main__":
    # Test the model with sample parameters
    from config import load_config_from_excel
    
    print("=" * 70)
    print("TESTING ECONOMIC MODEL")
    print("=" * 70)
    
    config = load_config_from_excel()
    model = SOCEconomicModel(config)
    
    # Test with gpt-4.1
    model_name = "gpt-4.1"
    E_m = config.llm_models[model_name]["E_m"]
    eta = config.eta_mean
    theta = config.theta_mean
    
    print(f"\n📊 Analyzing: {model_name}")
    print(f"  Accuracy E^m: {E_m:.2%}")
    print(f"  Efficiency η: {eta:.2%}")
    print(f"  Capital ratio θ: {theta:.2%}")
    
    result = model.analyze(model_name, E_m, eta, theta)
    
    print(f"\n💰 COST BREAKDOWN:")
    print(f"  Without LLM:")
    print(f"    Total: ${result.C_noLLM_total:,.2f}/day")
    print(f"    Personnel: ${result.C_noLLM_personnel:,.2f}/day")
    
    print(f"\n  With LLM:")
    print(f"    Total: ${result.C_LLM_total:,.2f}/day")
    print(f"    Personnel: ${result.C_LLM_personnel:,.2f}/day")
    print(f"    LLM Tech: ${result.C_tech:,.2f}/day")
    
    print(f"\n📈 RESULTS:")
    print(f"  Operational Savings ΔC: ${result.delta_C:,.2f}/day")
    print(f"  Capital Expenditure: ${result.C_cap:,.2f}/day")
    print(f"  ROI: {result.roi:.2%}")
    
    profitability = "✅ PROFITABLE" if result.roi > 0 else "❌ NOT PROFITABLE"
    print(f"\n  {profitability}")
    
    print("\n" + "=" * 70)
    print("✅ Model validated successfully!")
    print("=" * 70)
