import json
from typing import Dict, Any, List

def calculate_banking_metrics(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Standardized calculation for Banking metrics.
    raw_data expected keys:
    - nPL_group3, nPL_group4, nPL_group5
    - total_loans
    - demand_deposits, total_deposits
    - net_interest_income, avg_earning_assets
    - operating_expenses, total_operating_income
    """
    results = {}
    try:
        # NPL Ratio
        bad_debt = raw_data.get('nPL_group3', 0) + raw_data.get('nPL_group4', 0) + raw_data.get('nPL_group5', 0)
        total_loans = raw_data.get('total_loans', 0)
        results['npl_ratio'] = (bad_debt / total_loans) * 100 if total_loans > 0 else 0
        
        # CASA Ratio
        results['casa_ratio'] = (raw_data.get('demand_deposits', 0) / raw_data.get('total_deposits', 1)) * 100
        
        # NIM
        results['nim'] = (raw_data.get('net_interest_income', 0) / raw_data.get('avg_earning_assets', 1)) * 100
        
        # CIR
        results['cir'] = (raw_data.get('operating_expenses', 0) / raw_data.get('total_operating_income', 1)) * 100
        
        # LLR (Loan Loss Reserve) Coverage
        reserve = raw_data.get('loan_loss_reserve', 0)
        results['llr_coverage'] = (reserve / bad_debt) * 100 if bad_debt > 0 else 0
        
        return {k: round(v, 2) for k, v in results.items()}
    except Exception as e:
        return {"error": str(e)}

def build_banking_analysis_pack(base_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Higher-level helper to calculate growth and deltas between current and previous periods.
    """
    results = {}
    try:
        # Growth calculations
        fields = ["total_assets", "total_loans", "total_deposits", "profit_after_tax", "net_interest_income"]
        for f in fields:
            curr = base_data.get(f, 0)
            prev = base_data.get(f + "_prev", 0)
            if prev and prev != 0:
                results[f + "_growth"] = round(((curr - prev) / prev) * 100, 2)
            else:
                results[f + "_growth"] = 0
        
        # Calculate metrics for both periods
        curr_raw = {k: v for k, v in base_data.items() if not k.endswith("_prev")}
        prev_raw = {k[:-5]: v for k, v in base_data.items() if k.endswith("_prev")}
        
        m_curr = calculate_banking_metrics(curr_raw)
        m_prev = calculate_banking_metrics(prev_raw)
        
        results["current_metrics"] = m_curr
        results["previous_metrics"] = m_prev
        
        # Deltas (BPS)
        for k in m_curr:
            if k in m_prev and isinstance(m_curr[k], (int, float)):
                results[k + "_delta_bps"] = round((m_curr[k] - m_prev[k]) * 100, 0)
        
        return results
    except Exception as e:
        return {"error": str(e)}

def calculate_real_estate_metrics(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Standardized calculation for Real Estate metrics.
    raw_data expected keys:
    - inventory (Hàng tồn kho)
    - advances_from_customers (Người mua trả tiền trước)
    - total_debt (Nợ vay - ngắn & dài hạn)
    - equity (Vốn chủ sở hữu)
    - revenue, gross_profit
    """
    results = {}
    try:
        # Debt / Equity
        results['debt_to_equity'] = raw_data.get('total_debt', 0) / raw_data.get('equity', 1)
        
        # Inventory / Total Assets
        results['inventory_to_assets'] = (raw_data.get('inventory', 0) / raw_data.get('total_assets', 1)) * 100
        
        # Advances / Inventory (Measure of pre-sales success)
        results['presales_coverage'] = (raw_data.get('advances_from_customers', 0) / raw_data.get('inventory', 1)) * 100
        
        # Gross Margin
        results['gross_margin'] = (raw_data.get('gross_profit', 0) / raw_data.get('revenue', 1)) * 100
        
        return {k: round(v, 2) for k, v in results.items()}
    except Exception as e:
        return {"error": str(e)}

def calculate_securities_metrics(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Standardized calculation for Securities (Brokerage) metrics.
    raw_data expected keys:
    - margin_loans (Cho vay margin)
    - brokerage_revenue, brokerage_expenses
    - fvtpl_gains, fvtpl_losses
    - afs_gains
    """
    results = {}
    try:
        # Brokerage Profit Margin
        broker_profit = raw_data.get('brokerage_revenue', 0) - raw_data.get('brokerage_expenses', 0)
        results['brokerage_margin'] = (broker_profit / raw_data.get('brokerage_revenue', 1)) * 100
        
        # FVTPL Performance
        fvtpl_net = raw_data.get('fvtpl_gains', 0) - raw_data.get('fvtpl_losses', 0)
        results['fvtpl_net_return'] = fvtpl_net
        
        # Margin Loans / Equity
        results['margin_to_equity'] = raw_data.get('margin_loans', 0) / raw_data.get('equity', 1)
        
        return {k: round(v, 2) for k, v in results.items()}
    except Exception as e:
        return {"error": str(e)}

def calculate_general_metrics(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Standardized calculation for Manufacturing/Retail (General) metrics.
    """
    results = {}
    try:
        results['gross_margin'] = (raw_data.get('gross_profit', 0) / raw_data.get('revenue', 1)) * 100
        results['net_margin'] = (raw_data.get('net_profit', 0) / raw_data.get('revenue', 1)) * 100
        results['roe'] = (raw_data.get('net_profit', 0) / raw_data.get('equity', 1)) * 100
        results['current_ratio'] = raw_data.get('current_assets', 0) / raw_data.get('current_liabilities', 1)
        
        return {k: round(v, 2) for k, v in results.items()}
    except Exception as e:
        return {"error": str(e)}
