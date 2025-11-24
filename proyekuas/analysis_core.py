# analysis_core.py
"""
Pusat Logika Analisis Statistik Versi 2.1 (Fix & Stable)
- Perbaikan Logika Hausman Test (Anti-Crash).
- Perbaikan Import Statsmodels versi terbaru.
- Penanganan Error yang lebih kuat.
"""

import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.stats.api import het_breuschpagan, jarque_bera
from statsmodels.stats.outliers_influence import variance_inflation_factor
# PERBAIKAN IMPORT: Dipisahkan sesuai versi statsmodels terbaru
from statsmodels.tsa.stattools import adfuller
from statsmodels.stats.diagnostic import acorr_ljungbox, het_arch
from statsmodels.stats.stattools import durbin_watson
from scipy import stats

# Library untuk Auto-ARIMA
import pmdarima as pm

# Library Wajib untuk Panel Data
from linearmodels.panel import PanelOLS, RandomEffects, PooledOLS
from linearmodels.panel import compare

import json

# Helper untuk mengonversi hasil ke format JSON yang aman
class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        if hasattr(obj, 'summary_as_text'):
            return str(obj.summary_as_text())
        return super(NpEncoder, self).default(obj)

def results_to_json(data):
    """Mengonversi dictionary hasil, membersihkan nilai non-serializable."""
    return json.dumps(data, cls=NpEncoder, indent=2)

# ==============================================================================
# 1. ANALISIS CROSS-SECTION (DENGAN PERBAIKAN OTOMATIS)
# ==============================================================================

def run_cross_section_analysis(df, y_var, x_vars):
    results = {
        "analysis_type": "Cross-Section",
        "model_type": "OLS",
        "inputs": {"y": y_var, "x": x_vars},
        "assumption_tests": {},
        "model_estimation": {},
        "notes": []
    }

    try:
        y = df[y_var]
        X = sm.add_constant(df[x_vars])

        # 1. Estimasi Model OLS (Awal, untuk mendapatkan residual)
        model_initial = sm.OLS(y, X).fit()
        residuals = model_initial.resid

        # --- 2. Lakukan Uji Asumsi ---
        use_robust_errors = False

        # Uji Multikolinearitas (VIF)
        try:
            vif_data = [{"feature": X.columns[i], "VIF": variance_inflation_factor(X.values, i)} for i in range(1, X.shape[1])]
            results["assumption_tests"]["multicollinearity_vif"] = vif_data
            if any(v['VIF'] > 10 for v in vif_data):
                results["notes"].append("Peringatan: Terdeteksi multikolinearitas tinggi (VIF > 10).")
        except Exception:
            pass # Skip VIF jika gagal hitung

        # Uji Homoskedastisitas (Breusch-Pagan)
        bp_test = het_breuschpagan(residuals, model_initial.model.exog)
        bp_pvalue = bp_test[1]
        results["assumption_tests"]["homoskedasticity_breusch_pagan"] = {"stat": bp_test[0], "p_value": bp_pvalue}
        if bp_pvalue < 0.05:
            use_robust_errors = True
            results["notes"].append("Info: Terdeteksi heteroskedastisitas (Breusch-Pagan p < 0.05). Menggunakan Robust Standard Errors (HC1).")
        
        # Uji Independensi Error (Durbin-Watson)
        dw_stat = durbin_watson(residuals)
        results["assumption_tests"]["autocorrelation_durbin_watson"] = {"statistic": dw_stat}
        if dw_stat < 1.5 or dw_stat > 2.5:
            use_robust_errors = True
            results["notes"].append("Info: Terdeteksi autokorelasi (Durbin-Watson tidak mendekati 2). Menggunakan Robust Standard Errors.")

        # Uji Normalitas Residual (Jarque-Bera)
        jb_test = jarque_bera(residuals)
        results["assumption_tests"]["normality_jarque_bera"] = {"stat": jb_test[0], "p_value": jb_test[1]}
        if jb_test[1] < 0.05:
            results["notes"].append("Peringatan: Residual mungkin tidak terdistribusi normal (Jarque-Bera p < 0.05).")

        # --- 3. Estimasi Model Final (Dengan Perbaikan jika perlu) ---
        if use_robust_errors:
            results["model_type"] = "OLS with Robust Standard Errors (HC1)"
            model_final = sm.OLS(y, X).fit(cov_type='HC1')
        else:
            results["model_type"] = "OLS (Standard)"
            model_final = model_initial 

        # --- 4. Kumpulkan Hasil Estimasi ---
        results["model_estimation"] = {
            "summary_table": model_final.summary().as_text(),
            "coefficients": model_final.params.to_dict(),
            "p_values": model_final.pvalues.to_dict(),
            "r_squared": model_final.rsquared,
        }

    except Exception as e:
        results["error"] = str(e)

    return results


# ==============================================================================
# 2. ANALISIS TIME SERIES (DENGAN AUTO-ARIMA)
# ==============================================================================

def run_arima_analysis(df, y_var, **kwargs):
    results = {
        "analysis_type": "Time Series (Auto-ARIMA)",
        "inputs": {"y": y_var},
        "stationarity_tests": {},
        "model_selection": {},
        "assumption_tests_on_residuals": {},
        "model_estimation": {},
        "notes": [],
    }

    try:
        series = df[y_var].dropna()

        # 1. Uji Stasioneritas (ADF)
        adf_result = adfuller(series)
        results["stationarity_tests"]["adf_test_original_data"] = {
            "stat": adf_result[0], "p_value": adf_result[1],
            "conclusion": "Stasioner" if adf_result[1] < 0.05 else "Tidak Stasioner"
        }

        # 2. Pemilihan Model Otomatis (Auto-ARIMA)
        m_period = kwargs.get('seasonal_m', 1) 
        seasonal = True if m_period > 1 else False
        
        auto_model = pm.auto_arima(
            series,
            start_p=1, start_q=1,
            test='adf', max_p=3, max_q=3,
            m=m_period, d=None, seasonal=seasonal,
            start_P=0, D=None, trace=False,
            error_action='ignore', suppress_warnings=True, stepwise=True
        )

        results["model_selection"] = {
            "chosen_order": auto_model.order,
            "aic": auto_model.aic()
        }
        results["model_type"] = f"ARIMA{auto_model.order}"

        # 3. Uji Asumsi pada Residual
        residuals = auto_model.resid()
        
        # Uji Autokorelasi (Ljung-Box)
        lb_test = acorr_ljungbox(residuals, lags=[10], return_df=True)
        lb_pvalue = lb_test.iloc[0]['lb_pvalue']
        results["assumption_tests_on_residuals"]["autocorrelation_ljung_box"] = {
            "stat": lb_test.iloc[0]['lb_stat'], "p_value": lb_pvalue,
            "conclusion": "Residual independen" if lb_pvalue > 0.05 else "Residual memiliki autokorelasi"
        }

        # Uji Heteroskedastisitas (ARCH)
        arch_test = het_arch(residuals)
        arch_pvalue = arch_test[1]
        results["assumption_tests_on_residuals"]["heteroskedasticity_arch"] = {
            "stat": arch_test[0], "p_value": arch_pvalue,
            "conclusion": "Residual homoskedastisitas" if arch_pvalue > 0.05 else "Residual heteroskedastisitas"
        }

        # 4. Kumpulkan Hasil Estimasi
        results["model_estimation"] = {
            "summary_table": auto_model.summary().as_text(),
            "coefficients": auto_model.params().to_dict(),
            "p_values": auto_model.pvalues().to_dict(),
            "aic": auto_model.aic(),
        }

    except Exception as e:
        results["error"] = str(e)

    return results


# ==============================================================================
# 3. ANALISIS DATA PANEL (DENGAN PEMILIHAN OTOMATIS)
# ==============================================================================

def run_panel_analysis(df, y_var, x_vars, entity_col, time_col):
    results = {
        "analysis_type": "Panel Data",
        "inputs": {"y": y_var, "x": x_vars, "entity": entity_col, "time": time_col},
        "models": {},
        "model_selection_tests": {},
        "final_model_diagnostics": {},
        "final_model_estimation": {},
        "chosen_model": None,
        "notes": [],
        "error": None
    }

    try:
        # --- 1. Persiapan Data ---
        df_panel = df.copy()
        try:
            # Set MultiIndex (entity, time)
            df_panel = df_panel.set_index([entity_col, time_col])
        except KeyError:
             # Debugging info jika kolom tidak ketemu
            cols_found = list(df_panel.columns)
            raise ValueError(f"Kolom '{entity_col}' atau '{time_col}' tidak ditemukan. Kolom yang terbaca: {cols_found}")
            
        y = df_panel[y_var]
        X = sm.add_constant(df_panel[x_vars])

        # --- 2. Estimasi Model Kandidat ---
        model_cem = PooledOLS(y, X).fit()
        results["models"]["cem_pooled_ols"] = model_cem.summary.as_text()
        
        model_fem = PanelOLS(y, X, entity_effects=True).fit()
        results["models"]["fem_fixed_effects"] = model_fem.summary.as_text()
        
        model_rem = RandomEffects(y, X).fit()
        results["models"]["rem_random_effects"] = model_rem.summary.as_text()

        # --- 3. Uji Pemilihan Model (Hausman Test) ---
        # PERBAIKAN PENTING: Inisialisasi variabel agar tidak error jika try gagal
        hausman_stat = None
        hausman_pvalue = None

        try:
            hausman_compare = compare({"FEM": model_fem, "REM": model_rem})
            hausman_test = hausman_compare.hausman
            
            hausman_stat = hausman_test.stat
            hausman_pvalue = hausman_test.pval
        except Exception as e:
            # Fallback jika matriks singular/data kurang
            hausman_pvalue = 0.0 
            results["notes"].append(f"Uji Hausman gagal dihitung (Error: {str(e)}). Default ke FEM.")
            
        results["model_selection_tests"]["hausman_test"] = {"stat": hausman_stat, "p_value": hausman_pvalue}

        # Logika Pemilihan
        if hausman_pvalue is not None and hausman_pvalue < 0.05:
            results["chosen_model"] = "Fixed Effects Model (FEM)"
            base_model = model_fem
        else:
            results["chosen_model"] = "Random Effects Model (REM)"
            base_model = model_rem

        # --- 4. Uji Asumsi pada Model Terpilih ---
        is_hetero = False
        is_autocorr = False
        is_cross_dep = False
        
        diagnostics = {}
        
        # Uji Heteroskedastisitas (Breusch-Pagan)
        try:
            bp_test = het_breuschpagan(base_model.resids, base_model.model.exog)
            bp_pvalue = bp_test[1]
            diagnostics["heteroskedasticity_breusch_pagan"] = {"stat": bp_test[0], "p_value": bp_pvalue}
            if bp_pvalue < 0.05: is_hetero = True
        except:
            pass # Skip jika gagal

        # Uji Autokorelasi (Wooldridge Test) - LOCAL IMPORT AGAR AMAN
        try:
            from linearmodels.panel.diagnostics import wooldridge_test
            wd_test = wooldridge_test(base_model)
            wd_pvalue = wd_test.pval
            diagnostics["autocorrelation_wooldridge"] = {"stat": wd_test.stat, "p_value": wd_pvalue}
            if wd_pvalue < 0.05: is_autocorr = True
        except ImportError:
            diagnostics["autocorrelation_wooldridge"] = {"error": "Fitur ini butuh linearmodels v5+"}
        except Exception as e:
            diagnostics["autocorrelation_wooldridge"] = {"error": f"Gagal: {str(e)}"}

        # Uji Korelasi Antar Unit (Pesaran CD) - LOCAL IMPORT AGAR AMAN
        try:
            from linearmodels.panel.diagnostics import pesaran_cd_test
            cd_test = pesaran_cd_test(base_model)
            cd_pvalue = cd_test.pval
            diagnostics["cross_sectional_dependence_pesaran_cd"] = {"stat": cd_test.stat, "p_value": cd_pvalue}
            if cd_pvalue < 0.05: is_cross_dep = True
        except ImportError:
             diagnostics["cross_sectional_dependence_pesaran_cd"] = {"error": "Fitur ini butuh linearmodels v5+"}
        except Exception as e:
            diagnostics["cross_sectional_dependence_pesaran_cd"] = {"error": f"Gagal: {str(e)}"}
        
        results["final_model_diagnostics"] = diagnostics

        # --- 5. Estimasi Model FINAL (Dengan Perbaikan Otomatis) ---
        cov_type = 'unadjusted'
        
        if is_autocorr or is_cross_dep:
            cov_type = 'clustered' # Cluster by entity
            results["notes"].append("Info: Terdeteksi Autokorelasi/Cross-Dep. Menggunakan Clustered Errors.")
        elif is_hetero:
            cov_type = 'robust'
            results["notes"].append("Info: Terdeteksi Heteroskedastisitas. Menggunakan Robust Errors.")
        
        # Fit ulang model akhir dengan cov_type yang sesuai
        if results["chosen_model"] == "Fixed Effects Model (FEM)":
            final_model = PanelOLS(y, X, entity_effects=True).fit(cov_type=cov_type)
        else:
            final_model = RandomEffects(y, X).fit(cov_type=cov_type)

        # --- 6. Kumpulkan Hasil Estimasi Final ---
        results["final_model_estimation"] = {
            "summary_table": final_model.summary.as_text(),
            "coefficients": final_model.params.to_dict(),
            "p_values": final_model.pvalues.to_dict(),
            "r_squared_within": final_model.rsquared_within,
            "r_squared_overall": final_model.rsquared_overall,
        }

    except Exception as e:
        results["error"] = str(e)
    
    return results


# ==============================================================================
# 4. FUNGSI UTAMA (ROUTER)
# ==============================================================================

def run_analysis(df, y_var, x_vars, data_type, **kwargs):
    if data_type == 'cross_section':
        analysis_result = run_cross_section_analysis(df, y_var, x_vars)
    
    elif data_type == 'time_series':
        analysis_result = run_arima_analysis(df, y_var, **kwargs)
    
    elif data_type == 'panel':
        entity_col = kwargs.get('entity_col')
        time_col = kwargs.get('time_col')
        
        if not entity_col or not time_col:
            analysis_result = {"error": "Analisis panel memerlukan 'entity_col' dan 'time_col'."}
        else:
            analysis_result = run_panel_analysis(df, y_var, x_vars, entity_col, time_col)
    
    else:
        analysis_result = {"error": f"Jenis data tidak dikenal: {data_type}"}
        
    return results_to_json(analysis_result)