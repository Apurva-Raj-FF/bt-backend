"""
Strategy Service Module

This module handles all strategy-related operations including:
- Strategy execution
- Strategy saving and retrieval
- Portfolio management
- Data processing and analysis
"""

from app.strategy.schemas import (
    SaveStrategyRequest,
)
import subprocess
import json
import os
import sys
from app.database.models import InputPortfolio, PortfolioStats, CalYear
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.database.database import SessionLocal

def run_script(session_id: str, user_token: str, payload: dict) -> dict:
    """
    Execute a Python script with the given parameters and return database results.
    
    Args:
        session_id (str): Unique identifier for the execution session
        user_token (str): Authentication token for the user
        payload (dict): Data to be processed by the script
        
    Returns:
        dict: Execution results with database records in specified format
            {
                "status": str,  # "Success" or "Failure"
                "output": dict,  # Database records if successful
                "error": str,   # Error message if failed
                "strategy_id": str  # Session ID if successful
            }
    """
    try:
        # First execute the script to populate the database
        script_path = os.getenv('SCRIPT_PATH')
        if not os.path.exists(script_path):
            return {"status": "Failure", "error": "Script file not found"}

        cmd = [sys.executable, script_path, session_id, user_token, json.dumps(payload)]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise Exception(f"Script execution failed: {result.stderr}")

        # Now query the database to get the inserted records
        db_session = SessionLocal()
        try:
            # Get input portfolio data
            input_portfolio = db_session.query(InputPortfolio).filter(
                InputPortfolio.session_id == session_id
            ).first()

            if not input_portfolio:
                raise Exception("No input portfolio found for the session")

            # Convert input portfolio to dictionary format
            ippf_data = {
                "session_id": input_portfolio.session_id,
                "user_id": input_portfolio.user_id,
                "insert_time": input_portfolio.insert_time,
                "strat_name": input_portfolio.strat_name,
                "id": str(input_portfolio.id),
                "strat_name_alias": input_portfolio.strat_name_alias
            }
            
            # Add year data
            for year in range(1999, 2023):
                year_col = f"y_{year}"
                if hasattr(input_portfolio, year_col):
                    ippf_data[str(year)] = getattr(input_portfolio, year_col)

            # Get portfolio stats
            portfolio_stats = db_session.query(PortfolioStats).filter(
                PortfolioStats.session_id == session_id
            ).all()

            pfst_data = []
            for stat in portfolio_stats:
                stat_dict = {
                    "session_id": stat.session_id,
                    "insert_time": stat.insert_time,
                    "strat_name": stat.strat_name,
                    "nyears": stat.nyears,
                    "cagr_mean": str(stat.cagr_mean) if stat.cagr_mean is not None else None,
                    "cagr_median": str(stat.cagr_median) if stat.cagr_median is not None else None,
                    "cagr_std": str(stat.cagr_std) if stat.cagr_std is not None else None,
                    "sharpe_ratio": str(stat.sharpe_ratio) if stat.sharpe_ratio is not None else None,
                    "ndatapoint": stat.ndatapoint,
                    "index_mean": str(stat.index_mean) if stat.index_mean is not None else None,
                    "index_median": str(stat.index_median) if stat.index_median is not None else None,
                    "index_std": str(stat.index_std) if stat.index_std is not None else None,
                    "index_SR": str(stat.index_SR) if stat.index_SR is not None else None,
                    "alpha_mean": str(stat.alpha_mean) if stat.alpha_mean is not None else None,
                    "alpha_median": str(stat.alpha_median) if stat.alpha_median is not None else None,
                    "alpha_std": str(stat.alpha_std) if stat.alpha_std is not None else None,
                    "alpha_SR": str(stat.alpha_SR) if stat.alpha_SR is not None else None,
                    "cagr_dwn_std": str(stat.cagr_dwn_std) if stat.cagr_dwn_std is not None else None,
                    "index_dwn_std": str(stat.index_dwn_std) if stat.index_dwn_std is not None else None,
                    "alpha_dwn_std": str(stat.alpha_dwn_std) if stat.alpha_dwn_std is not None else None,
                    "avg_no_stock": str(stat.avg_no_stock) if stat.avg_no_stock is not None else None,
                    "prob_0_15": str(stat.prob_0_15) if stat.prob_0_15 is not None else None,
                    "prob_0": str(stat.prob_0) if stat.prob_0 is not None else None,
                    "prob_0_7": str(stat.prob_0_7) if stat.prob_0_7 is not None else None,
                    "prob_0_15p": str(stat.prob_0_15p) if stat.prob_0_15p is not None else None,
                    "prob_0_25": str(stat.prob_0_25) if stat.prob_0_25 is not None else None,
                    "prob_0_5": str(stat.prob_0_5) if stat.prob_0_5 is not None else None,
                    "prob_1": str(stat.prob_1) if stat.prob_1 is not None else None,
                    "alpha_0_15": str(stat.alpha_0_15) if stat.alpha_0_15 is not None else None,
                    "alpha_0": str(stat.alpha_0) if stat.alpha_0 is not None else None,
                    "alpha_0_7": str(stat.alpha_0_7) if stat.alpha_0_7 is not None else None,
                    "alpha_0_15_pos": str(stat.alpha_0_15_pos) if stat.alpha_0_15_pos is not None else None,
                    "alpha_0_25": str(stat.alpha_0_25) if stat.alpha_0_25 is not None else None,
                    "alpha_0_5": str(stat.alpha_0_5) if stat.alpha_0_5 is not None else None,
                    "alpha_1": stat.alpha_1,
                    "highest_pcagr": str(stat.highest_pcagr) if stat.highest_pcagr is not None else None,
                    "lowest_pcagr": str(stat.lowest_pcagr) if stat.lowest_pcagr is not None else None,
                    "highest_index": str(stat.highest_index) if stat.highest_index is not None else None,
                    "lowest_index": str(stat.lowest_index) if stat.lowest_index is not None else None,
                    "highest_alpha": str(stat.highest_alpha) if stat.highest_alpha is not None else None,
                    "lowest_alpha": str(stat.lowest_alpha) if stat.lowest_alpha is not None else None,
                    "id": stat.id,
                    "mod_list_pct": stat.mod_list_pct
                }
                pfst_data.append(stat_dict)

            # Get calendar year data
            cal_years = db_session.query(CalYear).filter(
                CalYear.session_id == session_id
            ).all()

            calyears_data = []
            for cal_year in cal_years:
                cal_dict = {
                    "session_id": cal_year.session_id,
                    "user_id": cal_year.user_id,
                    "year": cal_year.year,
                    "portfolio_cagr": str(cal_year.portfolio_cagr) if cal_year.portfolio_cagr is not None else None,
                    "index_cagr": str(cal_year.index_cagr) if cal_year.index_cagr is not None else None,
                    "id": cal_year.id
                }
                calyears_data.append(cal_dict)

            # Construct the final output
            output = {
                "ippf": ippf_data,
                "pfst": pfst_data,
                "calyears": calyears_data
            }

            return {
                "status": "Success",
                "output": output,
                "strategy_id": session_id
            }

        except Exception as e:
            db_session.rollback()
            raise e
        finally:
            db_session.close()

    except Exception as e:
        return {"status": "Failure", "error": str(e)}
    
def save_strategy_service(request: SaveStrategyRequest, db: Session) -> dict:
    """
    Save or update a strategy in the database.
    
    Args:
        request (SaveStrategyRequest): Strategy data to save
        db (Session): Database session
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException: If strategy is not found
    """
    portfolio_entry = db.query(InputPortfolio).filter(InputPortfolio.session_id == request.session_id).first()
    
    if not portfolio_entry:
        raise HTTPException(status_code=404, detail="Strategy not found")
    portfolio_entry.strat_name_alias = request.strat_name_alias
    portfolio_entry.isPublic = request.isPublic
    db.commit()
    
    return {"message": "Strategy updated successfully"}

def get_all_strategies_user_service(user_id: int, page: int, page_size: int, db: Session) -> dict:
    """
    Get paginated strategies for a specific user.
    
    Args:
        user_id (int): ID of the user
        page (int): Page number
        page_size (int): Number of items per page
        db (Session): Database session
        
    Returns:
        dict: Paginated list of strategies with metadata
    """
    # Calculate offset
    offset = (page - 1) * page_size
    
    # Get total count
    total_count = db.query(InputPortfolio).filter(
        InputPortfolio.user_id == user_id,
        InputPortfolio.strat_name_alias.isnot(None)
    ).count()
    
    # Get paginated strategies
    strategies = db.query(
        InputPortfolio.strat_name,
        InputPortfolio.strat_name_alias,
        InputPortfolio.session_id
    ).filter(
        InputPortfolio.user_id == user_id,
        InputPortfolio.strat_name_alias.isnot(None)
    ).offset(offset).limit(page_size).all()

    if not strategies and page == 1:
        raise HTTPException(status_code=404, detail="No valid strategies found for this user")

    strategies_list = [
        {"strategy": strategy.strat_name, "name": strategy.strat_name_alias, "strategy_id": strategy.session_id}
        for strategy in strategies
    ]

    return {
        "strategies": strategies_list,
        "pagination": {
            "total": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": (total_count + page_size - 1) // page_size
        }
    }

def get_all_strategies_service(page: int, page_size: int, db: Session) -> dict:
    """
    Get all public strategies with pagination.
    
    Args:
        page (int): Page number
        page_size (int): Number of items per page
        db (Session): Database session
        
    Returns:
        dict: Paginated list of strategies with metadata
    """
    # Calculate offset
    offset = (page - 1) * page_size
    
    # Get total count
    total_count = db.query(InputPortfolio).filter(
        InputPortfolio.strat_name_alias.isnot(None)
    ).count()
    
    # Get paginated strategies
    strategies = db.query(
        InputPortfolio.strat_name,
        InputPortfolio.strat_name_alias,
        InputPortfolio.session_id
    ).filter(
        InputPortfolio.strat_name_alias.isnot(None)
    ).offset(offset).limit(page_size).all()

    if not strategies and page == 1:
        raise HTTPException(status_code=404, detail="No valid strategies found")

    strategies_list = [
        {"strategy": strategy.strat_name, "name": strategy.strat_name_alias, "strategy_id": strategy.session_id}
        for strategy in strategies
    ]

    return {
        "strategies": strategies_list,
        "pagination": {
            "total": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": (total_count + page_size - 1) // page_size
        }
    }

def get_strategy_service(strategy_id: str, db: Session) -> dict:
    """
    Get detailed information about a specific strategy.
    
    Args:
        strategy_id (str): ID of the strategy to retrieve
        db (Session): Database session
        
    Returns:
        dict: Detailed strategy information including:
            {
                "ippf": {
                    "session_id": str,
                    "user_id": int,
                    "insert_time": datetime,
                    "strat_name": str,
                    "strat_name_alias": str,
                    "isPublic": bool,
                    "y_1999": float,
                    ...
                },
                "pfst": [
                    {
                        "nyears": int,
                        "cagr_mean": float,
                        "cagr_median": float,
                        "cagr_std": float,
                        "sharpe_ratio": float,
                        "alpha_mean": float,
                        "alpha_median": float,
                        "alpha_std": float,
                        "highest_pcagr": float,
                        "lowest_pcagr": float,
                        "highest_alpha": float,
                        "lowest_alpha": float
                    }
                ],
                "calyears": [
                    {
                        "year": int,
                        "portfolio_cagr": float,
                        "index_cagr": float
                    }
                ]
            }
            
    Raises:
        HTTPException: If strategy is not found
    """
    strategy = db.query(InputPortfolio).filter(
        InputPortfolio.session_id == strategy_id
    ).first()
    if not strategy:
        raise HTTPException(
            status_code=404, 
            detail=f"Strategy with ID {strategy_id} not found"
        )

    stats = db.query(PortfolioStats).filter(
        PortfolioStats.session_id == strategy_id
    ).all() or []

    yearly_data = db.query(CalYear).filter(
        CalYear.session_id == strategy_id
    ).order_by(CalYear.year.asc()).all() or []
    
    # Format portfolio composition data
    portfolio_composition = {}
    for year in range(1999, 2023):
        column_name = f"y_{year}"
        if hasattr(InputPortfolio, column_name):
            value = getattr(strategy, column_name, None)
            portfolio_composition[column_name] = value

    # Format performance metrics by year range
    performance_metrics = []
    for stat in stats:
        if stat:  # Only process if stat is not None
            metrics = {
                "nyears": stat.nyears,
                "cagr_mean": stat.cagr_mean,
                "cagr_median": stat.cagr_median,
                "cagr_std": stat.cagr_std,
                "sharpe_ratio": stat.sharpe_ratio,
                "alpha_mean": stat.alpha_mean,
                "alpha_median": stat.alpha_median,
                "alpha_std": stat.alpha_std,
                "highest_pcagr": stat.highest_pcagr,
                "lowest_pcagr": stat.lowest_pcagr,
                "highest_alpha": stat.highest_alpha,
                "lowest_alpha": stat.lowest_alpha
            }
            performance_metrics.append(metrics)

    # Format yearly performance data
    formatted_yearly_data = []
    for data in yearly_data:
        if data:  # Only process if data is not None
            yearly_perf = {
                "year": data.year,
                "portfolio_cagr": data.portfolio_cagr,
                "index_cagr": data.index_cagr
            }
            formatted_yearly_data.append(yearly_perf)

    # Prepare the final response
    response = {
        "ippf": {
            "session_id": strategy.session_id,
            "user_id": strategy.user_id,
            "insert_time": strategy.insert_time,
            "strat_name": strategy.strat_name,
            "strat_name_alias": strategy.strat_name_alias,
            "isPublic": strategy.isPublic,
            **portfolio_composition  # Include all the year columns
        },
        "pfst": performance_metrics,
        "calyears": formatted_yearly_data
    }
    return response