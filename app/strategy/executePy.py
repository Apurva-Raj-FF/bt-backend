import sys
import os

# Add the backend folder to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import json
from sqlalchemy.orm import Session
from app.database.database import SessionLocal
from app.database.models import InputPortfolio, PortfolioStats, CalYear
from datetime import datetime

def process_strategy(session: Session, session_id: str, user_token: str, data: dict):
    """Process the strategy and insert a new row into portfolio_investment_rules"""
    new_session_id = str(session_id)
    
    # Create base object
    input_portfolio = InputPortfolio(
        session_id=new_session_id,
        user_id=user_token,
        insert_time=str(datetime.utcnow()),
        strat_name=json.dumps(data),
        strat_name_alias=None,
        isPublic=False
    )
    
    # Handle year values properly
    for year in range(1999, 2023):
        # Get the value from data (default to empty list if not found)
        value = data.get(str(year), [])
        
        # Ensure the value is always a list
        if not isinstance(value, list):
            value = [value] if value is not None else []
        
        # Convert the list to a JSON string representation
        # This will store "[]" for empty lists in the database
        setattr(input_portfolio, f"y_{year}", json.dumps(value))
    
    session.add(input_portfolio)
    session.commit()
    return new_session_id

def backtest_and_create_stats(session: Session, session_id: str, strat_name: str):
    """Perform backtesting and insert portfolio statistics for a 10-year horizon"""
    for horizon in range(1, 11):
        portfolio_stats = PortfolioStats(
            session_id=session_id,
            insert_time=str(datetime.utcnow()),
            strat_name=json.dumps(strat_name),
            nyears=horizon,
            cagr_mean=0.1 * horizon,  # Placeholder
            sharpe_ratio=0.5 * horizon,  # Placeholder
            ndatapoints=100 + 10 * horizon,  # Placeholder
        )
        session.add(portfolio_stats)
    session.commit()

def populate_cal_year_data(session: Session, session_id: str, user_id: str):
    """Populate cal_year for each year from 2000 to 2022"""
    for year in range(2000, 2023):
        cal_year = CalYear(
            session_id=session_id,
            user_id=user_id,
            year=year,
            portfolio_cagr=0.05 * (year - 2000 + 1),  # Placeholder
            index_cagr=0.04 * (year - 2000 + 1),  # Placeholder
        )
        session.add(cal_year)
    session.commit()

def main():
    if len(sys.argv) < 4:
        print("Usage: python executePy.py <session_id> <user_token> <json_data>")
        sys.exit(1)

    session_id = sys.argv[1]
    user_token = sys.argv[2]
    json_data = sys.argv[3]

    try:
        data = json.loads(json_data)
    except json.JSONDecodeError:
        print("Error: Invalid JSON data")
        sys.exit(1)

    db_session = SessionLocal()
    try:
        new_session_id = process_strategy(db_session, session_id, user_token, data)
        backtest_and_create_stats(db_session, new_session_id, data)
        populate_cal_year_data(db_session, new_session_id, user_token)

        print(f"Backtest completed for session: {new_session_id}")

    except Exception as e:
        db_session.rollback()
        print(f"Error: {e}")

    finally:
        db_session.close()

if __name__ == "__main__":
    main()
