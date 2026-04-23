"""
Visualization Module for LLM SOC ROI Simulator
Generates publication-quality plots using Matplotlib/Seaborn
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from typing import Dict, List, Tuple, Optional
from pathlib import Path

# Set publication-quality defaults
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['font.size'] = 10
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['axes.labelsize'] = 11
plt.rcParams['axes.titlesize'] = 12
plt.rcParams['xtick.labelsize'] = 9
plt.rcParams['ytick.labelsize'] = 9
plt.rcParams['legend.fontsize'] = 9
plt.rcParams['figure.titlesize'] = 14

# Color palette (professional, colorblind-friendly)
COLORS = {
    'profit': '#2ecc71',  # Green
    'loss': '#e74c3c',    # Red
    'neutral': '#95a5a6', # Gray
    'primary': '#3498db', # Blue
    'secondary': '#9b59b6', # Purple
    'warning': '#f39c12', # Orange
    'cv_low': '#3498db',
    'cv_moderate': '#2ecc71',
    'cv_high': '#f39c12',
    'cv_extreme': '#e74c3c',
}


class ROIVisualizer:
    """
    Generates all visualizations for ROI analysis.
    """
    
    def __init__(self, output_dir: str = "outputs/plots"):
        """
        Initialize visualizer.
        
        Parameters:
        -----------
        output_dir : str
            Directory to save plots
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def save_fig(self, filename: str):
        """Save figure with consistent naming"""
        path = self.output_dir / filename
        plt.savefig(path, bbox_inches='tight', facecolor='white')
        print(f"  💾 Saved: {filename}")
    
    # ===== 1. ROI HEATMAP WITH CONFIDENCE CONTOURS =====
    def plot_roi_heatmap(self, results: Dict, model_name: str, cv_level: float,
                        accuracy_range: Tuple[float, float] = (0.3, 1.0),
                        efficiency_range: Tuple[float, float] = (0.5, 0.9),
                        resolution: int = 50):
        """
        Generate 2D ROI heatmap: Accuracy (E^m) vs Efficiency (η).
        Overlay confidence contours for P(ROI>0) = 50%, 80%, 95%.
        
        Parameters:
        -----------
        results : Dict
            Monte Carlo simulation results
        model_name : str
            Model name for title
        cv_level : float
            Uncertainty level
        accuracy_range : Tuple
            (min, max) accuracy for grid
        efficiency_range : Tuple
            (min, max) efficiency for grid
        resolution : int
            Grid resolution
        """
        from model import SOCEconomicModel
        from config import load_config_from_excel
        
        config = load_config_from_excel()
        model = SOCEconomicModel(config)
        
        # Create grid
        accuracy_vals = np.linspace(*accuracy_range, resolution)
        efficiency_vals = np.linspace(*efficiency_range, resolution)
        A, E = np.meshgrid(accuracy_vals, efficiency_vals)
        
        # Compute ROI for each grid point
        ROI_grid = np.zeros_like(A)
        theta = config.theta_mean
        
        for i in range(resolution):
            for j in range(resolution):
                analysis = model.analyze(model_name, A[i,j], E[i,j], theta)
                ROI_grid[i,j] = analysis.roi
        
        # Create plot
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Heatmap
        im = ax.contourf(A, E, ROI_grid, levels=20, cmap='RdYlGn', alpha=0.8)
        cbar = plt.colorbar(im, ax=ax, label='Expected ROI')
        
        # Add zero contour (break-even line)
        contour_zero = ax.contour(A, E, ROI_grid, levels=[0], colors='black', 
                                  linewidths=2, linestyles='--')
        ax.clabel(contour_zero, inline=True, fmt='Break-even', fontsize=9)
        
        # Styling
        ax.set_xlabel('Accuracy E^m (fraction of correct outputs)', fontsize=11)
        ax.set_ylabel('Efficiency η (fraction of time saved)', fontsize=11)
        ax.set_title(f'ROI Heatmap: {model_name} (CV={cv_level:.0%}, θ={theta:.0%})', 
                    fontsize=13, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle=':')
        
        plt.tight_layout()
        self.save_fig(f"heatmap_roi_{model_name}_cv{int(cv_level*100)}.png")
        plt.close()
    
    # ===== 2. PROFITABILITY PROBABILITY CURVES =====
    def plot_profitability_curves(self, all_cv_results: Dict[float, Dict], model_name: str):
        """
        Plot P(ROI > 0 | CV) vs θ (capital expenditure ratio).
        One curve per CV level.
        
        Parameters:
        -----------
        all_cv_results : Dict[float, Dict]
            Results for all CV levels
        model_name : str
            Model name for title
        """
        fig, ax = plt.subplots(figsize=(12, 7))
        
        cv_colors = {
            0.05: COLORS['cv_low'],
            0.25: COLORS['cv_moderate'],
            0.50: COLORS['cv_high'],
            1.00: COLORS['cv_extreme'],
        }
        
        for cv_level, results in all_cv_results.items():
            # Compute profitability probability for different theta values
            theta_range = np.linspace(0, 0.5, 100)
            prob_profit = []
            
            for theta_val in theta_range:
                # Recompute ROI with different theta
                delta_C = results['delta_C']
                C_noLLM = results['C_noLLM']
                C_cap_new = theta_val * C_noLLM
                roi_new = (delta_C - C_cap_new) / C_cap_new
                
                # Handle division by zero
                roi_new = np.where(C_cap_new == 0, np.inf, roi_new)
                
                prob = np.mean(roi_new > 0)
                prob_profit.append(prob)
            
            # Plot curve
            ax.plot(theta_range, prob_profit, 
                   label=f'CV = {cv_level:.0%}',
                   color=cv_colors.get(cv_level, COLORS['primary']),
                   linewidth=2.5)
        
        # Add threshold lines
        ax.axhline(y=0.80, color='gray', linestyle='--', linewidth=1, alpha=0.5, label='80% confidence')
        ax.axhline(y=0.50, color='gray', linestyle=':', linewidth=1, alpha=0.5, label='50% confidence')
        
        # Styling
        ax.set_xlabel('Capital Expenditure Ratio θ (fraction of baseline cost)', fontsize=11)
        ax.set_ylabel('P(ROI > 0) - Probability of Profitability', fontsize=11)
        ax.set_title(f'Profitability Probability: {model_name}', fontsize=13, fontweight='bold')
        ax.set_xlim(0, 0.5)
        ax.set_ylim(0, 1.05)
        ax.grid(True, alpha=0.3)
        ax.legend(loc='upper right', framealpha=0.95)
        
        plt.tight_layout()
        self.save_fig(f"profitability_curves_{model_name}.png")
        plt.close()
    
    # ===== 3. WATERFALL CHART (COST BREAKDOWN) =====
    def plot_waterfall_breakdown(self, breakdown, model_name: str):
        """
        Waterfall chart showing cost transformation from baseline to net ROI.
        
        Parameters:
        -----------
        breakdown : CostBreakdown
            Cost breakdown from model.analyze()
        model_name : str
            Model name
        """
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # Define waterfall steps
        categories = [
            'Baseline\nCost',
            'Personnel\nSavings',
            'LLM\nAPI Cost',
            'Capital\nExpenditure',
            'Net\nSavings'
        ]
        
        values = [
            breakdown.C_noLLM_total,
            -(breakdown.C_noLLM_personnel - breakdown.C_LLM_personnel),
            breakdown.C_tech,
            breakdown.C_cap,
            breakdown.delta_C - breakdown.C_cap
        ]
        
        # Compute running total
        running_total = [0]
        for i, val in enumerate(values[:-1]):
            if i == 0:
                running_total.append(val)
            else:
                running_total.append(running_total[-1] + val)
        
        # Colors
        colors = [COLORS['neutral'], COLORS['profit'], COLORS['loss'], 
                 COLORS['loss'], COLORS['profit'] if values[-1] > 0 else COLORS['loss']]
        
        # Plot bars
        for i, (cat, val, base) in enumerate(zip(categories, values, running_total)):
            if i == 0:  # Baseline
                ax.bar(i, val, bottom=0, color=colors[i], edgecolor='black', linewidth=1.5)
            else:  # Incremental changes
                ax.bar(i, abs(val), bottom=base if val > 0 else base + val, 
                      color=colors[i], edgecolor='black', linewidth=1.5)
                
                # Connection line
                if i < len(categories) - 1:
                    next_base = base + val
                    ax.plot([i, i+1], [next_base, next_base], 'k--', linewidth=1, alpha=0.5)
        
        # Add value labels
        for i, (val, base) in enumerate(zip(values, running_total)):
            if i == 0:
                label_y = val / 2
            else:
                label_y = base + val/2 if val > 0 else base + val/2
            
            ax.text(i, label_y, f'${abs(val):,.0f}', 
                   ha='center', va='center', fontsize=10, fontweight='bold',
                   bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # Styling
        ax.set_xticks(range(len(categories)))
        ax.set_xticklabels(categories, fontsize=10)
        ax.set_ylabel('Daily Cost (USD)', fontsize=11)
        ax.set_title(f'Cost Breakdown Waterfall: {model_name}', fontsize=13, fontweight='bold')
        ax.axhline(y=0, color='black', linewidth=1.5)
        ax.grid(axis='y', alpha=0.3)
        
        # ROI annotation
        roi_text = f"ROI = {breakdown.roi:.1%}"
        roi_color = COLORS['profit'] if breakdown.roi > 0 else COLORS['loss']
        ax.text(len(categories)-1, max(running_total) * 0.95, roi_text,
               fontsize=14, fontweight='bold', color=roi_color,
               bbox=dict(boxstyle='round', facecolor='white', edgecolor=roi_color, linewidth=2))
        
        plt.tight_layout()
        self.save_fig(f"waterfall_{model_name}.png")
        plt.close()
    
    # ===== 4. TORNADO DIAGRAM (SENSITIVITY ANALYSIS) =====
    def plot_tornado_diagram(self, base_results: Dict, model_name: str, 
                             parameters: List[str] = None,
                             variation: float = 0.20):
        """
        Tornado diagram showing impact of ±20% parameter changes on ROI.
        
        Parameters:
        -----------
        base_results : Dict
            Base case simulation results
        model_name : str
            Model name
        parameters : List[str], optional
            Parameters to analyze (default: all uncertain parameters)
        variation : float
            Percentage variation (0.20 = ±20%)
        """
        # This requires re-running simulations with perturbed parameters
        # For now, we'll use the samples to estimate sensitivity
        
        # Compute Spearman correlations as sensitivity measure
        params_data = {
            'Accuracy (E^m)': base_results['E_m_samples'],
            'Efficiency (η)': base_results['eta_samples'],
            'Capital Ratio (θ)': base_results['theta_samples'],
        }
        
        roi = base_results['roi']
        
        sensitivities = {}
        for param_name, param_values in params_data.items():
            # Spearman correlation (robust to non-linear relationships)
            corr, _ = stats.spearmanr(param_values, roi)
            sensitivities[param_name] = abs(corr)
        
        # Sort by impact
        sorted_params = sorted(sensitivities.items(), key=lambda x: x[1], reverse=True)
        
        # Plot
        fig, ax = plt.subplots(figsize=(10, 6))
        
        param_names = [p[0] for p in sorted_params]
        impacts = [p[1] for p in sorted_params]
        
        y_pos = np.arange(len(param_names))
        bars = ax.barh(y_pos, impacts, color=COLORS['primary'], edgecolor='black', linewidth=1.5)
        
        # Add value labels
        for i, (impact, bar) in enumerate(zip(impacts, bars)):
            ax.text(impact + 0.01, i, f'{impact:.3f}', 
                   va='center', fontsize=10, fontweight='bold')
        
        # Styling
        ax.set_yticks(y_pos)
        ax.set_yticklabels(param_names, fontsize=10)
        ax.set_xlabel('|Spearman Correlation with ROI|', fontsize=11)
        ax.set_title(f'Parameter Sensitivity (Tornado): {model_name}', 
                    fontsize=13, fontweight='bold')
        ax.grid(axis='x', alpha=0.3)
        ax.set_xlim(0, 1.0)
        
        plt.tight_layout()
        self.save_fig(f"tornado_{model_name}.png")
        plt.close()
    
    # ===== 5. CUMULATIVE DISTRIBUTION FUNCTION (CDF) =====
    def plot_roi_cdf(self, all_cv_results: Dict[float, Dict], model_name: str):
        """
        Plot cumulative distribution function of ROI for all CV levels.
        
        Parameters:
        -----------
        all_cv_results : Dict[float, Dict]
            Results for all CV levels
        model_name : str
            Model name
        """
        fig, ax = plt.subplots(figsize=(12, 7))
        
        cv_colors = {
            0.05: COLORS['cv_low'],
            0.25: COLORS['cv_moderate'],
            0.50: COLORS['cv_high'],
            1.00: COLORS['cv_extreme'],
        }
        
        for cv_level, results in all_cv_results.items():
            roi_values = results['roi']
            
            # Sort values for CDF
            sorted_roi = np.sort(roi_values)
            cdf_y = np.arange(1, len(sorted_roi) + 1) / len(sorted_roi)
            
            # Plot
            ax.plot(sorted_roi, cdf_y, 
                   label=f'CV = {cv_level:.0%}',
                   color=cv_colors.get(cv_level, COLORS['primary']),
                   linewidth=2.5)
        
        # Add reference lines
        ax.axvline(x=0, color='black', linestyle='--', linewidth=1.5, 
                  label='Break-even (ROI=0)')
        ax.axhline(y=0.5, color='gray', linestyle=':', linewidth=1, alpha=0.5)
        ax.axhline(y=0.95, color='gray', linestyle=':', linewidth=1, alpha=0.5)
        
        # Styling
        ax.set_xlabel('ROI (Return on Investment)', fontsize=11)
        ax.set_ylabel('Cumulative Probability P(ROI ≤ x)', fontsize=11)
        ax.set_title(f'ROI Cumulative Distribution: {model_name}', 
                    fontsize=13, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend(loc='lower right', framealpha=0.95)
        ax.set_xlim(-1, 2)
        ax.set_ylim(0, 1)
        
        # Format x-axis as percentage
        ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.0%}'))
        
        plt.tight_layout()
        self.save_fig(f"cdf_roi_{model_name}.png")
        plt.close()
    
    # ===== 6. VIOLIN PLOT (DISTRIBUTION COMPARISON) =====
    def plot_roi_violin(self, all_cv_results: Dict[float, Dict], model_name: str):
        """
        Violin plot showing ROI distributions across CV levels.
        
        Parameters:
        -----------
        all_cv_results : Dict[float, Dict]
            Results for all CV levels
        model_name : str
            Model name
        """
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Prepare data
        data_for_plot = []
        labels = []
        
        for cv_level in sorted(all_cv_results.keys()):
            results = all_cv_results[cv_level]
            roi_values = results['roi']
            
            # Clip extreme outliers for better visualization
            roi_clipped = np.clip(roi_values, -1, 3)
            
            data_for_plot.append(roi_clipped)
            labels.append(f'CV={cv_level:.0%}')
        
        # Create violin plot
        parts = ax.violinplot(data_for_plot, positions=range(len(labels)),
                             showmeans=True, showmedians=True, widths=0.7)
        
        # Color violins
        cv_color_list = [COLORS['cv_low'], COLORS['cv_moderate'], 
                        COLORS['cv_high'], COLORS['cv_extreme']]
        
        for i, pc in enumerate(parts['bodies']):
            pc.set_facecolor(cv_color_list[i])
            pc.set_alpha(0.7)
            pc.set_edgecolor('black')
            pc.set_linewidth(1.5)
        
        # Style median and mean lines
        parts['cmedians'].set_color('red')
        parts['cmedians'].set_linewidth(2)
        parts['cmeans'].set_color('blue')
        parts['cmeans'].set_linewidth(2)
        
        # Add break-even line
        ax.axhline(y=0, color='black', linestyle='--', linewidth=2, 
                  label='Break-even (ROI=0)')
        
        # Styling
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, fontsize=11)
        ax.set_ylabel('ROI (Return on Investment)', fontsize=11)
        ax.set_title(f'ROI Distribution (Violin Plot): {model_name}', 
                    fontsize=13, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, p: f'{y:.0%}'))
        
        # Add legend for mean/median
        from matplotlib.lines import Line2D
        legend_elements = [
            Line2D([0], [0], color='blue', linewidth=2, label='Mean'),
            Line2D([0], [0], color='red', linewidth=2, label='Median'),
            Line2D([0], [0], color='black', linestyle='--', linewidth=2, label='Break-even'),
        ]
        ax.legend(handles=legend_elements, loc='upper left', framealpha=0.95)
        
        plt.tight_layout()
        self.save_fig(f"violin_roi_{model_name}.png")
        plt.close()
    
    # ===== 7. VALUE AT RISK (VaR) CHART =====
    def plot_var_comparison(self, all_cv_results: Dict[float, Dict], model_name: str,
                           confidence_levels: List[float] = [0.05, 0.10, 0.25]):
        """
        Plot Value at Risk at different confidence levels.
        
        Parameters:
        -----------
        all_cv_results : Dict[float, Dict]
            Results for all CV levels
        model_name : str
            Model name
        confidence_levels : List[float]
            VaR confidence levels
        """
        fig, ax = plt.subplots(figsize=(10, 7))
        
        # Prepare data
        cv_levels = sorted(all_cv_results.keys())
        x_pos = np.arange(len(cv_levels))
        width = 0.25
        
        for i, conf_level in enumerate(confidence_levels):
            var_values = []
            
            for cv_level in cv_levels:
                results = all_cv_results[cv_level]
                roi_values = results['roi']
                
                # Compute VaR
                var_percentile = np.percentile(roi_values, conf_level * 100)
                var = -var_percentile if var_percentile < 0 else 0
                var_values.append(var)
            
            # Plot bars
            offset = (i - len(confidence_levels)/2 + 0.5) * width
            ax.bar(x_pos + offset, var_values, width, 
                  label=f'VaR {conf_level:.0%}',
                  edgecolor='black', linewidth=1)
        
        # Styling
        ax.set_xticks(x_pos)
        ax.set_xticklabels([f'CV={cv:.0%}' for cv in cv_levels], fontsize=10)
        ax.set_ylabel('Value at Risk (as positive loss)', fontsize=11)
        ax.set_title(f'Value at Risk Analysis: {model_name}', 
                    fontsize=13, fontweight='bold')
        ax.legend(loc='upper left', framealpha=0.95)
        ax.grid(axis='y', alpha=0.3)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, p: f'{y:.0%}'))
        
        plt.tight_layout()
        self.save_fig(f"var_{model_name}.png")
        plt.close()
    
    # ===== 8. MULTI-MODEL COMPARISON =====
    def plot_model_comparison_scatter(self, all_models_results: Dict[str, Dict],
                                     cv_level: float = 0.25):
        """
        Scatter plot comparing multiple models: Cost vs Accuracy vs ROI.
        
        Parameters:
        -----------
        all_models_results : Dict[str, Dict[float, Dict]]
            Results for all models and CV levels
        cv_level : float
            Which CV level to plot
        """
        fig, ax = plt.subplots(figsize=(14, 9))
        
        model_data = []
        
        for model_name, cv_results in all_models_results.items():
            if cv_level not in cv_results:
                continue
            
            results = cv_results[cv_level]
            
            # Compute summary statistics
            mean_roi = np.mean(results['roi'])
            mean_accuracy = np.mean(results['E_m_samples'])
            mean_cost = np.mean(results['C_LLM'])
            
            model_data.append({
                'model': model_name,
                'roi': mean_roi,
                'accuracy': mean_accuracy,
                'cost': mean_cost,
            })
        
        df = pd.DataFrame(model_data)
        
        # Create scatter plot
        scatter = ax.scatter(df['cost'], df['accuracy'], 
                           s=np.abs(df['roi']) * 1000,  # Bubble size proportional to |ROI|
                           c=df['roi'], cmap='RdYlGn', vmin=-0.5, vmax=0.5,
                           alpha=0.7, edgecolors='black', linewidth=2)
        
        # Add model labels
        for idx, row in df.iterrows():
            ax.annotate(row['model'], (row['cost'], row['accuracy']),
                       fontsize=8, ha='center', va='bottom',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='white', 
                               alpha=0.7, edgecolor='gray'))
        
        # Colorbar
        cbar = plt.colorbar(scatter, ax=ax, label='Mean ROI')
        cbar.ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, p: f'{y:.0%}'))
        
        # Styling
        ax.set_xlabel('Mean Daily Cost with LLM (USD)', fontsize=11)
        ax.set_ylabel('Mean Accuracy E^m', fontsize=11)
        ax.set_title(f'Model Comparison (CV={cv_level:.0%}): Cost vs Accuracy vs ROI',
                    fontsize=13, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, p: f'{y:.0%}'))
        
        # Add legend for bubble sizes
        handles, labels = scatter.legend_elements(prop="sizes", alpha=0.6, num=4)
        legend = ax.legend(handles, ['Low ROI', '', '', 'High |ROI|'], 
                          loc="upper right", title="ROI Magnitude", framealpha=0.95)
        
        plt.tight_layout()
        self.save_fig(f"comparison_scatter_cv{int(cv_level*100)}.png")
        plt.close()
    
    # ===== 9. GENERATE ALL PLOTS FOR A MODEL =====
    def generate_all_plots(self, all_cv_results: Dict[float, Dict], 
                          breakdown: 'CostBreakdown', model_name: str):
        """
        Generate all visualization types for a single model.
        
        Parameters:
        -----------
        all_cv_results : Dict[float, Dict]
            Results for all CV levels
        breakdown : CostBreakdown
            Cost breakdown for deterministic case
        model_name : str
            Model name
        """
        print(f"\n📊 Generating plots for {model_name}...")
        
        # Select moderate uncertainty (CV=25%) for some plots
        moderate_results = all_cv_results.get(0.25)
        
        if moderate_results is None:
            print(f"  ⚠ No results found for CV=25%, skipping some plots")
            return
        
        # Generate each plot
        try:
            print("  1/8 ROI Heatmap...")
            self.plot_roi_heatmap(moderate_results, model_name, 0.25)
        except Exception as e:
            print(f"  ❌ Heatmap failed: {e}")
        
        try:
            print("  2/8 Profitability Curves...")
            self.plot_profitability_curves(all_cv_results, model_name)
        except Exception as e:
            print(f"  ❌ Profitability curves failed: {e}")
        
        try:
            print("  3/8 Waterfall Chart...")
            self.plot_waterfall_breakdown(breakdown, model_name)
        except Exception as e:
            print(f"  ❌ Waterfall failed: {e}")
        
        try:
            print("  4/8 Tornado Diagram...")
            self.plot_tornado_diagram(moderate_results, model_name)
        except Exception as e:
            print(f"  ❌ Tornado failed: {e}")
        
        try:
            print("  5/8 CDF Plot...")
            self.plot_roi_cdf(all_cv_results, model_name)
        except Exception as e:
            print(f"  ❌ CDF failed: {e}")
        
        try:
            print("  6/8 Violin Plot...")
            self.plot_roi_violin(all_cv_results, model_name)
        except Exception as e:
            print(f"  ❌ Violin failed: {e}")
        
        try:
            print("  7/8 VaR Chart...")
            self.plot_var_comparison(all_cv_results, model_name)
        except Exception as e:
            print(f"  ❌ VaR failed: {e}")
        
        print("  ✅ All plots generated!")


if __name__ == "__main__":
    print("✅ Visualization module ready!")
    print("   Available plots:")
    print("   1. ROI Heatmap (Accuracy × Efficiency)")
    print("   2. Profitability Curves (θ vs P(ROI>0))")
    print("   3. Waterfall Cost Breakdown")
    print("   4. Tornado Sensitivity Diagram")
    print("   5. Cumulative Distribution Function (CDF)")
    print("   6. Violin Plot (distribution comparison)")
    print("   7. Value at Risk (VaR) Chart")
    print("   8. Multi-Model Scatter Comparison")
