"""
Monte Carlo Simulation Engine
Implements uncertainty quantification via Monte Carlo sampling (paper Section 3.4)
"""

import numpy as np
import pandas as pd
from tqdm import tqdm
from typing import Dict, List, Tuple
import pickle
from pathlib import Path

from distributions import UncertainParameter, sample_beta, sample_gamma
from model import SOCEconomicModel, CostBreakdown


class MonteCarloSimulator:
    """
    Monte Carlo simulator for ROI uncertainty quantification.
    Runs simulations across all CV levels (5%, 25%, 50%, 100%).
    """
    
    def __init__(self, config, n_iterations: int = 10000, random_seed: int = 42):
        """
        Initialize Monte Carlo simulator.
        
        Parameters:
        -----------
        config : SOCConfig
            Configuration from Excel
        n_iterations : int
            Number of Monte Carlo iterations per CV level
        random_seed : int
            Random seed for reproducibility
        """
        self.config = config
        self.n_iterations = n_iterations
        self.random_seed = random_seed
        self.model = SOCEconomicModel(config)
        
        np.random.seed(random_seed)
    
    def simulate_model(self, model_name: str, cv_level: float, 
                      verbose: bool = True) -> Dict[str, np.ndarray]:
        """
        Run Monte Carlo simulation for a specific model and CV level.
        
        Parameters:
        -----------
        model_name : str
            LLM model to simulate
        cv_level : float
            Coefficient of variation (e.g., 0.25 for 25% uncertainty)
        verbose : bool
            Show progress bar
            
        Returns:
        --------
        Dict[str, np.ndarray]
            Dictionary with simulation results:
            - 'roi': Array of ROI values
            - 'delta_C': Operational savings
            - 'C_noLLM': Baseline costs
            - 'C_LLM': Costs with LLM
            - 'eta_samples': Efficiency samples
            - 'theta_samples': Capital ratio samples
        """
        
        # Get model parameters from Excel
        E_m_mean = self.config.llm_models[model_name]["E_m"]
        eta_mean = self.config.eta_mean  # From paper: 0.70 (30% reduction)
        theta_mean = self.config.theta_mean  # Default: 0.10
        
        # Initialize arrays for results
        results = {
            'roi': np.zeros(self.n_iterations),
            'delta_C': np.zeros(self.n_iterations),
            'C_noLLM': np.zeros(self.n_iterations),
            'C_LLM': np.zeros(self.n_iterations),
            'C_cap': np.zeros(self.n_iterations),
            'eta_samples': np.zeros(self.n_iterations),
            'theta_samples': np.zeros(self.n_iterations),
            'E_m_samples': np.zeros(self.n_iterations),
        }
        
        # Create uncertain parameters
        # E^m (accuracy): Beta distribution (bounded in [0,1])
        E_m_param = UncertainParameter(E_m_mean, cv_level, "beta", f"E^m_{model_name}")
        
        # η (efficiency): Beta distribution (bounded in [0,1])  
        eta_param = UncertainParameter(eta_mean, cv_level, "beta", "eta")
        
        # θ (capital ratio): Beta distribution (bounded in [0,1])
        theta_param = UncertainParameter(theta_mean, cv_level, "beta", "theta")
        
        # Progress bar
        iterator = tqdm(range(self.n_iterations), desc=f"Simulating {model_name} (CV={cv_level:.0%})") \
                   if verbose else range(self.n_iterations)
        
        for i in iterator:
            # Sample uncertain parameters
            E_m_sample = E_m_param.sample(1)[0]
            eta_sample = eta_param.sample(1)[0]
            theta_sample = theta_param.sample(1)[0]
            
            # Store samples for analysis
            results['E_m_samples'][i] = E_m_sample
            results['eta_samples'][i] = eta_sample
            results['theta_samples'][i] = theta_sample
            
            # Run economic model
            analysis = self.model.analyze(model_name, E_m_sample, eta_sample, theta_sample)
            
            # Store results
            results['roi'][i] = analysis.roi
            results['delta_C'][i] = analysis.delta_C
            results['C_noLLM'][i] = analysis.C_noLLM_total
            results['C_LLM'][i] = analysis.C_LLM_total
            results['C_cap'][i] = analysis.C_cap
        
        return results
    
    def run_all_cv_levels(self, model_name: str) -> Dict[float, Dict]:
        """
        Run simulations across all uncertainty levels.
        
        Parameters:
        -----------
        model_name : str
            LLM model to simulate
            
        Returns:
        --------
        Dict[float, Dict]
            Results for each CV level
        """
        print(f"\n{'='*70}")
        print(f"MONTE CARLO SIMULATION: {model_name}")
        print(f"{'='*70}")
        print(f"  Iterations per CV level: {self.n_iterations:,}")
        print(f"  Uncertainty levels: {[f'{cv:.0%}' for cv in self.config.cv_levels]}")
        
        all_results = {}
        
        for cv_level in self.config.cv_levels:
            results = self.simulate_model(model_name, cv_level, verbose=True)
            all_results[cv_level] = results
            
            # Print summary statistics
            roi_mean = np.mean(results['roi'])
            roi_median = np.median(results['roi'])
            roi_std = np.std(results['roi'])
            p_profitable = np.mean(results['roi'] > 0)
            
            print(f"\n  CV={cv_level:.0%} Summary:")
            print(f"    ROI: μ={roi_mean:.2%}, median={roi_median:.2%}, σ={roi_std:.2%}")
            print(f"    P(ROI > 0) = {p_profitable:.2%}")
        
        print(f"\n{'='*70}")
        print(f"✅ Simulation complete for {model_name}!")
        print(f"{'='*70}\n")
        
        return all_results
    
    def compute_probability_of_profit(self, results: Dict[str, np.ndarray], 
                                      target_roi: float = 0.0) -> float:
        """
        Compute P(ROI > target_roi | CV) - equation (16) from paper.
        
        Parameters:
        -----------
        results : Dict
            Simulation results
        target_roi : float
            Target ROI threshold (0.0 = break-even)
            
        Returns:
        --------
        float
            Probability of exceeding target ROI
        """
        return np.mean(results['roi'] > target_roi)
    
    def compute_value_at_risk(self, results: Dict[str, np.ndarray], 
                             confidence_level: float = 0.05) -> float:
        """
        Compute Value at Risk (VaR) at given confidence level - equation (17) from paper.
        
        VaR_z(ROI) = -inf{y ∈ ℝ : P(ROI < y) > z}
        
        Parameters:
        -----------
        results : Dict
            Simulation results
        confidence_level : float
            Confidence level (0.05 = 5th percentile)
            
        Returns:
        --------
        float
            VaR (as positive loss, e.g., 0.20 = 20% loss)
        """
        roi_samples = results['roi']
        percentile_value = np.percentile(roi_samples, confidence_level * 100)
        
        # Return as positive loss if negative
        return -percentile_value if percentile_value < 0 else 0.0
    
    def save_results(self, results: Dict, filename: str):
        """
        Save simulation results to disk.
        
        Parameters:
        -----------
        results : Dict
            Simulation results
        filename : str
            Output filename (will be saved in outputs/cached_results/)
        """
        output_path = Path("outputs/cached_results") / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'wb') as f:
            pickle.dump(results, f)
        
        print(f"💾 Results saved to: {output_path}")
    
    def load_results(self, filename: str) -> Dict:
        """
        Load previously saved results.
        
        Parameters:
        -----------
        filename : str
            Filename to load
            
        Returns:
        --------
        Dict
            Simulation results
        """
        input_path = Path("outputs/cached_results") / filename
        
        with open(input_path, 'rb') as f:
            results = pickle.load(f)
        
        print(f"📂 Results loaded from: {input_path}")
        return results
    
    def export_to_dataframe(self, results: Dict[float, Dict], model_name: str) -> pd.DataFrame:
        """
        Export simulation results to pandas DataFrame for analysis.
        
        Parameters:
        -----------
        results : Dict[float, Dict]
            Results for all CV levels
        model_name : str
            Model name
            
        Returns:
        --------
        pd.DataFrame
            Long-format DataFrame with all samples
        """
        rows = []
        
        for cv_level, cv_results in results.items():
            n_samples = len(cv_results['roi'])
            
            for i in range(n_samples):
                rows.append({
                    'model': model_name,
                    'cv_level': cv_level,
                    'iteration': i,
                    'roi': cv_results['roi'][i],
                    'delta_C': cv_results['delta_C'][i],
                    'C_noLLM': cv_results['C_noLLM'][i],
                    'C_LLM': cv_results['C_LLM'][i],
                    'C_cap': cv_results['C_cap'][i],
                    'E_m': cv_results['E_m_samples'][i],
                    'eta': cv_results['eta_samples'][i],
                    'theta': cv_results['theta_samples'][i],
                })
        
        df = pd.DataFrame(rows)
        return df


def run_multi_model_comparison(simulator: MonteCarloSimulator, 
                               model_names: List[str]) -> Dict[str, Dict]:
    """
    Run simulations for multiple models and compare.
    
    Parameters:
    -----------
    simulator : MonteCarloSimulator
        Configured simulator
    model_names : List[str]
        List of model names to compare
        
    Returns:
    --------
    Dict[str, Dict]
        Results for each model
    """
    all_model_results = {}
    
    for model_name in model_names:
        results = simulator.run_all_cv_levels(model_name)
        all_model_results[model_name] = results
    
    return all_model_results


if __name__ == "__main__":
    from config import load_config_from_excel
    
    print("=" * 70)
    print("MONTE CARLO SIMULATION - TEST RUN")
    print("=" * 70)
    
    # Load configuration
    config = load_config_from_excel()
    
    # Create simulator (use fewer iterations for testing)
    simulator = MonteCarloSimulator(config, n_iterations=1000, random_seed=42)
    
    # Test with top 3 models
    test_models = ["gpt-4.1", "gpt-4-turbo", "Grok-3"]
    
    # Run simulations
    results = run_multi_model_comparison(simulator, test_models)
    
    # Save results
    simulator.save_results(results, "test_simulation_results.pkl")
    
    print("\n✅ Test simulation complete!")
    print(f"   Results saved to: outputs/cached_results/test_simulation_results.pkl")
