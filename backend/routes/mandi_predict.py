from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from inference import (
    load_artifacts,
    predict_crop_price,
    get_msp_gap_comparison,
    get_crop_ranking,
    get_crop_list,
    get_state_list,
    get_latest_date_in_dataset
)

router = APIRouter(tags=["Mandi Price Prediction & Ranking"])

@router.on_event("startup")
def startup_load_models():
    """
    Ensure the ML model, preprocessors, and datasets are loaded at application startup.
    """
    print("Loading ML models and data for Mandi Prediction...")
    load_artifacts()

def validate_inputs(commodity: Optional[str] = None, state: Optional[str] = None):
    """
    Validate input crop and state.
    Rejects unknown crops or states with clear error messages.
    """
    valid_crops = get_crop_list()
    valid_states = get_state_list()
    
    if commodity is not None:
        comm_clean = commodity.strip().lower()
        if comm_clean not in valid_crops:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid commodity '{commodity}'. Must be one of: {', '.join(valid_crops)}"
            )
            
    if state is not None:
        state_clean = state.strip().lower()
        # Find exact case-matching state name
        state_exact = next((s for s in valid_states if s.lower() == state_clean), None)
        if not state_exact:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid state '{state}'. Must be one of: {', '.join(valid_states[:15])}..."
            )
        return state_exact
        
    return None

@router.get("/predict")
def predict_endpoint(
    commodity: str = Query(..., description="Name of the Kharif crop"),
    state: str = Query(..., description="State name"),
    date: Optional[str] = Query(None, description="Date for prediction (YYYY-MM-DD), defaults to latest available date")
):
    """
    Returns predicted modal price for a single crop/state/date.
    """
    state_exact = validate_inputs(commodity=commodity, state=state)
    commodity_clean = commodity.strip().lower()
    
    try:
        pred_price = predict_crop_price(commodity_clean, state_exact, date)
        ref_date = date or get_latest_date_in_dataset().strftime("%Y-%m-%d")
        return {
            "commodity": commodity_clean,
            "state": state_exact,
            "date": ref_date,
            "predicted_price": round(pred_price, 2)
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference error: {str(e)}")

@router.get("/msp-comparison")
def msp_comparison_endpoint(
    commodity: str = Query(..., description="Name of the Kharif crop"),
    state: str = Query(..., description="State name")
):
    """
    Returns predicted price, MSP, and gap percentage for a single crop/state.
    """
    state_exact = validate_inputs(commodity=commodity, state=state)
    commodity_clean = commodity.strip().lower()
    
    try:
        res = get_msp_gap_comparison(commodity_clean, state_exact)
        return res
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference error: {str(e)}")

@router.get("/crop-ranking")
def crop_ranking_endpoint(
    state: str = Query(..., description="State name"),
    volatility_weight: float = Query(50.0, description="Penalization weight for crop price volatility")
):
    """
    Returns the ranked list of all 14 kharif crops for that state.
    Crops are ranked based on a combined score: expected profit margin vs volatility risk.
    """
    state_exact = validate_inputs(state=state)
    
    try:
        ranking = get_crop_ranking(state_exact, volatility_weight=volatility_weight)
        return {
            "state": state_exact,
            "volatility_weight": volatility_weight,
            "ranking": ranking
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ranking logic error: {str(e)}")
