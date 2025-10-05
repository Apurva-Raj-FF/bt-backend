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
import ast
from app.database.models import InputPortfolio, PortfolioStats, CalYear
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.database.database import SessionLocal
from sqlalchemy import or_

def _coerce_to_dict(possibly_json: str):
    """Attempt to coerce various string formats into a Python dict.
    Tries JSON first, then Python-literal (ast.literal_eval). Returns dict or None.
    """
    if not possibly_json or not isinstance(possibly_json, str):
        return None
    # Fast path: proper JSON
    try:
        parsed = json.loads(possibly_json)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass

    # Try Python literal style (single quotes, unquoted True/False/None, etc.)
    try:
        parsed = ast.literal_eval(possibly_json)
        if isinstance(parsed, dict):
            return parsed
        # Sometimes strat_name is a stringified JSON nested inside quotes
        if isinstance(parsed, str):
            try:
                nested = json.loads(parsed)
                if isinstance(nested, dict):
                    return nested
            except Exception:
                try:
                    nested2 = ast.literal_eval(parsed)
                    if isinstance(nested2, dict):
                        return nested2
                except Exception:
                    pass
    except Exception:
        pass

    # Last resort: naive replacements to move towards valid JSON
    try:
        sanitized = possibly_json.replace("'", '"')
        parsed = json.loads(sanitized)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass

    return None

def format_query_from_strat_name(strat_name: str) -> str:
    """
    Format the strat_name field into a readable query string.
    The strat_name contains JSON (or Python-literal) with filters that need to be parsed and formatted.
    
    Args:
        strat_name (str): JSON/Python-literal string containing query parameters
        
    Returns:
        str: Formatted, human-readable query string
    """
    try:
        if not strat_name:
            return "No query available"

        # Parse the data with tolerant coercion
        query_data = None
        # Direct JSON
        try:
            query_data = json.loads(strat_name)
        except Exception:
            query_data = _coerce_to_dict(strat_name)

        if not isinstance(query_data, dict):
            return "Invalid query format"

        # Some datasets may nest the query under a known key, try to unwrap
        if 'query' in query_data and isinstance(query_data['query'], (str, dict)):
            inner = query_data['query']
            if isinstance(inner, str):
                inner_parsed = _coerce_to_dict(inner)
                if isinstance(inner_parsed, dict):
                    query_data = inner_parsed
            elif isinstance(inner, dict):
                query_data = inner

        filters = query_data.get('filters')
        if not isinstance(filters, list) or len(filters) == 0:
            return "No filters defined"

        sign_map = {
            'gt': '>',
            'gte': '>=',
            'lt': '<',
            'lte': '<=',
            'eq': '=',
            'ne': '!='
        }

        formatted_filters = []
        for filter_item in filters:
            if not isinstance(filter_item, dict):
                continue
            data = filter_item.get('Data') or filter_item.get('data') or {}
            operator = filter_item.get('Operator') or filter_item.get('operator') or ''

            param = data.get('param') or {}
            param_name = param.get('name') or param.get('field') or 'Unknown'
            sign = data.get('sign') or data.get('op') or '='
            threshold = data.get('threshold')
            period = data.get('period', 1)  # Get the period (year) information

            # Render threshold nicely
            if isinstance(threshold, (list, tuple)):
                threshold_str = ','.join(map(str, threshold))
            else:
                threshold_str = str(threshold)

            readable_sign = sign_map.get(str(sign).lower(), sign)
            clause = f"{param_name} {period} Years {readable_sign} {threshold_str}".strip()
            if operator and isinstance(operator, str) and operator.strip():
                clause = f"{clause} {operator.strip()}"
            formatted_filters.append(clause)

        if formatted_filters:
            # Avoid trailing AND if user already appended
            result = ' '.join(formatted_filters).rstrip().rstrip('AND').rstrip()
            return result
        return "No valid filters found"

    except Exception as e:
        return f"Query parsing error: {str(e)}"

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
                InputPortfolio.strat_uuid == session_id
            ).first()

            if not input_portfolio:
                raise Exception("No input portfolio found for the session")

            # Convert input portfolio to dictionary format
            ippf_data = {
                "strat_uuid": input_portfolio.strat_uuid,
                "user_id": input_portfolio.user_id,
                "insert_time": input_portfolio.insert_time,
                "strat_name": input_portfolio.strat_name,
                "id": str(input_portfolio.id),
                "strat_name_alias": input_portfolio.strat_name_alias
            }
            
            # Add year data
            for year in range(1999, 2025):
                year_col = f"y_{year}"
                if hasattr(input_portfolio, year_col):
                    ippf_data[str(year)] = getattr(input_portfolio, year_col)

            # Get portfolio stats
            portfolio_stats = db_session.query(PortfolioStats).filter(
                PortfolioStats.strat_uuid == session_id
            ).all()

            pfst_data = []
            for stat in portfolio_stats:
                stat_dict = {
                    "nyears": stat.nyears,
                    # Frontend expects these names; map from new columns
                    "cagr_mean": stat.mean,
                    "cagr_median": stat.median,
                    "cagr_std": stat.std,
                    "sharpe_ratio": stat.sharpe,
                    "ndatapoints": stat.ndatapoints,

                    "index_mean": stat.index_mean,
                    "index_median": stat.index_median,
                    "index_std": stat.index_std,
                    "index_SR": stat.index_sharpe,

                    # Downside deviations
                    "cagr_dwn_std": stat.dwn_std_dev,
                    "index_dwn_std": stat.indx_dwn_std_dev,

                    # High/low summaries
                    "highest_pcagr": stat.highest_pcagr,
                    "lowest_pcagr": stat.lowest_pcagr,
                    "highest_index": stat.highest_index,
                    "lowest_index": stat.lowest_index,

                    # Keep id for table keys and any extra text
                    "id": stat.id,
                    "mod_list_pct": stat.mod_list_pct,
                    # For PDF query text if used elsewhere
                    "strat_name": stat.strat_name,
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
                    "portfolio_cagr": cal_year.portfolio_cagr,
                    "index_cagr": cal_year.index_cagr,
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
    portfolio_entry = db.query(InputPortfolio).filter(InputPortfolio.strat_uuid == request.session_id).first()
    
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
        InputPortfolio.strat_uuid,
    ).filter(
        InputPortfolio.user_id == user_id,
        InputPortfolio.strat_name_alias.isnot(None)
    ).offset(offset).limit(page_size).all()

    strategies_list = [
        {
            "strategy": strategy.strat_name,  # Raw query data
            "name": strategy.strat_name_alias,
            "strategy_id": strategy.strat_uuid,  # Use strat_uuid since no session_id
            "formatted_query": format_query_from_strat_name(strategy.strat_name),
        }
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

def get_all_strategies_service_old(page: int, page_size: int, db: Session) -> dict:
    """
    Get all public strategies with pagination.
    Only returns strategies that are public (isPublic=1) and have a strategy name alias.
    
    Args:
        page (int): Page number
        page_size (int): Number of items per page
        db (Session): Database session
        
    Returns:
        dict: Paginated list of strategies with metadata
    """
    # Calculate offset
    offset = (page - 1) * page_size
    
    # Get total count - only count strategies that are public and have an alias
    total_count = db.query(InputPortfolio).filter(
        InputPortfolio.isPublic == 1,  # MySQL tinyint(1) = 1 for true
        InputPortfolio.strat_name_alias.isnot(None),
        InputPortfolio.strat_name_alias != ""
    ).count()
    
    # Get paginated strategies - only get strategies that are public and have an alias
    strategies = db.query(
        InputPortfolio.strat_name,
        InputPortfolio.strat_name_alias,
        InputPortfolio.strat_uuid,
    ).filter(
        InputPortfolio.isPublic == 1,  # MySQL tinyint(1) = 1 for true
        InputPortfolio.strat_name_alias.isnot(None),
        InputPortfolio.strat_name_alias != ""
    ).offset(offset).limit(page_size).all()

    # Never 404 on list endpoints; return empty list when none
    strategies_list = [
        {
            "strategy": strategy.strat_name,  # Raw query data
            "name": strategy.strat_name_alias,
            "strategy_id": strategy.strat_uuid,  # Use strat_uuid since no session_id
            "formatted_query": format_query_from_strat_name(strategy.strat_name),
        }
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
    Only returns strategies that are public (isPublic=1) and have a strategy name alias.

    Args:
        page (int): Page number
        page_size (int): Number of items per page
        db (Session): Database session

    Returns:
        dict: Paginated list of strategies with metadata
    """
    # Calculate offset
    offset = (page - 1) * page_size

    # Add explicit ordering for consistent pagination results; using strat_uuid as an example
    query_base = db.query(
        InputPortfolio.strat_name,
        InputPortfolio.strat_name_alias,
        InputPortfolio.strat_uuid,
        InputPortfolio.id,
    ).filter(
        InputPortfolio.isPublic == 1,
        InputPortfolio.strat_name_alias.isnot(None),
        InputPortfolio.strat_name_alias != ""
    ).order_by(InputPortfolio.id)

    # Get total count efficiently (ensure there is an index on isPublic and strat_name_alias)
    total_count = query_base.with_entities(func.count(InputPortfolio.id)).scalar()

    # Fetch paginated results
    strategies = query_base.offset(offset).limit(page_size).all()

    strategies_list = [
        {
            "strategy": strategy.strat_name,
            "name": strategy.strat_name_alias,
            "strategy_id": strategy.strat_uuid,
            "formatted_query": format_query_from_strat_name(strategy.strat_name),
        }
        for strategy in strategies
    ]

    return {
        "strategies": strategies_list,
        "pagination": {
            "total": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": (total_count + page_size - 1) // page_size,
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
        InputPortfolio.strat_uuid == strategy_id,
    ).first()
    if not strategy:
        raise HTTPException(
            status_code=404, 
            detail=f"Strategy with ID {strategy_id} not found"
        )

    stats = db.query(PortfolioStats).filter(
        PortfolioStats.strat_uuid == strategy_id,
    ).all() or []

    yearly_data = db.query(CalYear).filter(
        CalYear.session_id == strategy_id,
    ).order_by(CalYear.year.asc()).all() or []
    
    # Format portfolio composition data
    portfolio_composition = {}
    for year in range(1999, 2025):
        column_name = f"y_{year}"
        if hasattr(InputPortfolio, column_name):
            value = getattr(strategy, column_name, None)
            portfolio_composition[column_name] = value

    # Format performance metrics by year range - MAP TO FRONTEND EXPECTED NAMES
    performance_metrics = []
    for stat in stats:
        if stat:  # Only process if stat is not None
            metrics = {
                "nyears": stat.nyears,
                # Map database columns to frontend expected names
                "cagr_mean": stat.mean,
                "cagr_median": stat.median,
                "cagr_std": stat.std,
                "sharpe_ratio": stat.sharpe,
                "cagr_dwn_std": stat.dwn_std_dev,
                
                "index_mean": stat.index_mean,
                "index_median": stat.index_median,
                "index_std": stat.index_std,
                "index_SR": stat.index_sharpe,
                "index_dwn_std": stat.indx_dwn_std_dev,
                
                "highest_pcagr": stat.highest_pcagr,
                "lowest_pcagr": stat.lowest_pcagr,
                "highest_index": stat.highest_index,
                "lowest_index": stat.lowest_index,
                
                # Keep original names for any other uses
                "alpha_mean": stat.alpha_mean,
                "alpha_median": stat.alpha_median,
                "alpha_std": stat.alpha_std,
                "alpha_sharpe": stat.alpha_sharpe,
                "highest_alpha": stat.highest_alpha,
                "lowest_alpha": stat.lowest_alpha,
                
                # Additional fields that might be needed
                "ndatapoints": stat.ndatapoints,
                "mod_list_pct": stat.mod_list_pct,
                "id": stat.id,
                "strat_name": stat.strat_name,
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
            "strat_uuid": strategy.strat_uuid,
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