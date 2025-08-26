from sqlalchemy import Column, String, Integer, Text, Double, BigInteger, TIMESTAMP, Enum, Boolean
from sqlalchemy.sql import func
from app.database.database import Base
from datetime import datetime
import enum

class UserRole(enum.Enum):
    ADMIN = "Admin"
    STANDARD_USER = "Standard User"
    GUEST = "Guest"

class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    mobile = Column(String(20), nullable=True)
    password_hash = Column(String(255), nullable=True)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.STANDARD_USER)
    google_id = Column(String(255), unique=True, nullable=True)
    is_verified = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(TIMESTAMP, nullable=False, default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, default=func.now(), onupdate=func.now())
    last_login_at = Column(TIMESTAMP, nullable=True)
    reset_token = Column(String(255), nullable=True)
    reset_token_expiry = Column(TIMESTAMP, nullable=True)

class InputPortfolio(Base):
    __tablename__ = "input_portfolio"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(250), nullable=False, index=True)
    user_id = Column(String(255), nullable=False)
    insert_time = Column(String(255), nullable=False)
    strat_name = Column(Text, nullable=False)
    strat_name_alias = Column(String(255), nullable=True)
    isPublic = Column(Boolean, nullable=False, default=False)

    # Columns for years from 1999 to 2022
    y_1999 = Column("1999", Text, nullable=True)
    y_2000 = Column("2000",Text, nullable=True)
    y_2001 = Column("2001",Text, nullable=True)
    y_2002 = Column("2002",Text, nullable=True)
    y_2003 = Column("2003",Text, nullable=True)
    y_2004 = Column("2004",Text, nullable=True)
    y_2005 = Column("2005",Text, nullable=True)
    y_2006 = Column("2006",Text, nullable=True)
    y_2007 = Column("2007",Text, nullable=True)
    y_2008 = Column("2008",Text, nullable=True)
    y_2009 = Column("2009",Text, nullable=True)
    y_2010 = Column("2010",Text, nullable=True)
    y_2011 = Column("2011",Text, nullable=True)
    y_2012 = Column("2012",Text, nullable=True)
    y_2013 = Column("2013",Text, nullable=True)
    y_2014 = Column("2014",Text, nullable=True)
    y_2015 = Column("2015",Text, nullable=True)
    y_2016 = Column("2016",Text, nullable=True)
    y_2017 = Column("2017",Text, nullable=True)
    y_2018 = Column("2018",Text, nullable=True)
    y_2019 = Column("2019",Text, nullable=True)
    y_2020 = Column("2020",Text, nullable=True)
    y_2021 = Column("2021",Text, nullable=True)
    y_2022 = Column("2022",Text, nullable=True)


class PortfolioStats(Base):
    __tablename__ = "portfolio_stats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Text, nullable=True)
    insert_time = Column(Text, nullable=True)
    strat_name = Column(Text, nullable=True)

    nyears = Column(Integer, nullable=True)
    cagr_mean = Column(Double, nullable=True)
    cagr_median = Column(Double, nullable=True)
    cagr_std = Column(Double, nullable=True)
    sharpe_ratio = Column(Double, nullable=True)
    ndatapoint = Column(Integer, nullable=True)

    index_mean = Column(Double, nullable=True)
    index_median = Column(Double, nullable=True)
    index_std = Column(Double, nullable=True)
    index_SR = Column(Double, nullable=True)

    alpha_mean = Column(Double, nullable=True)
    alpha_median = Column(Double, nullable=True)
    alpha_std = Column(Double, nullable=True)
    alpha_SR = Column(Double, nullable=True)

    cagr_dwn_std = Column(Double, nullable=True)
    index_dwn_std = Column(Double, nullable=True)
    alpha_dwn_std = Column(Double, nullable=True)

    avg_no_stock = Column(Double, nullable=True)

    prob_0_15 = Column(Double, nullable=True)
    prob_0 = Column(Double, nullable=True)
    prob_0_7 = Column(Double, nullable=True)
    prob_0_15p = Column(Double, nullable=True)
    prob_0_25 = Column(Double, nullable=True)
    prob_0_5 = Column(Double, nullable=True)
    prob_1 = Column(Double, nullable=True)

    alpha_0_15 = Column(Double, nullable=True)
    alpha_0 = Column(Double, nullable=True)
    alpha_0_7 = Column(Double, nullable=True)
    alpha_0_15_pos = Column(Double, nullable=True)
    alpha_0_25 = Column(Double, nullable=True)
    alpha_0_5 = Column(Double, nullable=True)
    alpha_1 = Column(Integer, nullable=True)

    highest_pcagr = Column(Double, nullable=True)
    lowest_pcagr = Column(Double, nullable=True)
    highest_index = Column(Double, nullable=True)
    lowest_index = Column(Double, nullable=True)
    highest_alpha = Column(Double, nullable=True)
    lowest_alpha = Column(Double, nullable=True)

    mod_list_pct = Column(Text, nullable=True)


class CalYear(Base):
    __tablename__ = "cal_year"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Text, nullable=True)
    user_id = Column(Text, nullable=True)
    year = Column(Integer, nullable=True)
    portfolio_cagr = Column(Double, nullable=True)
    index_cagr = Column(Double, nullable=True)