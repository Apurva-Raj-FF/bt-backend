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
    __tablename__ = "portfolio_investment_rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    # Columns as provided by user
    y_1997 = Column("1997", Text, nullable=True)
    y_1998 = Column("1998", Text, nullable=True)
    y_1999 = Column("1999", Text, nullable=True)
    y_2000 = Column("2000", Text, nullable=True)
    y_2001 = Column("2001", Text, nullable=True)
    y_2002 = Column("2002", Text, nullable=True)
    y_2003 = Column("2003", Text, nullable=True)
    y_2004 = Column("2004", Text, nullable=True)
    y_2005 = Column("2005", Text, nullable=True)
    y_2006 = Column("2006", Text, nullable=True)
    y_2007 = Column("2007", Text, nullable=True)
    y_2008 = Column("2008", Text, nullable=True)
    y_2009 = Column("2009", Text, nullable=True)
    y_2010 = Column("2010", Text, nullable=True)
    y_2011 = Column("2011", Text, nullable=True)
    y_2012 = Column("2012", Text, nullable=True)
    y_2013 = Column("2013", Text, nullable=True)
    y_2014 = Column("2014", Text, nullable=True)
    y_2015 = Column("2015", Text, nullable=True)
    y_2016 = Column("2016", Text, nullable=True)
    y_2017 = Column("2017", Text, nullable=True)
    y_2018 = Column("2018", Text, nullable=True)
    y_2019 = Column("2019", Text, nullable=True)
    y_2020 = Column("2020", Text, nullable=True)
    y_2021 = Column("2021", Text, nullable=True)
    y_2022 = Column("2022", Text, nullable=True)
    y_2023 = Column("2023", Text, nullable=True)
    y_2024 = Column("2024", Text, nullable=True)
    insert_time = Column("insert_time", Text, nullable=True)
    reference_file = Column("reference_file", Text, nullable=True)
    strat_name = Column("strat_name", Text, nullable=True)
    strat_uuid = Column("strat_uuid", Text, nullable=True)
    tag = Column("tag", Text, nullable=True)
    user_id = Column("user_id", Text, nullable=True)
    # Add the missing columns that should exist
    strat_name_alias = Column(String(255), nullable=True)
    isPublic = Column(Integer, nullable=False, default=0)  # tinyint(1) in MySQL

class PortfolioStats(Base):
    __tablename__ = "investment_rules_statistics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    # Columns as provided by user - using exact database column names
    alpha_0 = Column("alpha_0", Double, nullable=True)
    alpha_0_07 = Column("alpha_0.07", Double, nullable=True)
    alpha_0_15 = Column("alpha_0.15", Double, nullable=True)
    alpha_0_15_pos = Column("alpha_0_15_pos", Double, nullable=True)  # This one has underscore
    alpha_0_25 = Column("alpha_0.25", Double, nullable=True)
    alpha_0_5 = Column("alpha_0.5", Double, nullable=True)
    alpha_1 = Column("alpha_1", Integer, nullable=True)  # This is int, not double
    alpha_dwn_std_dev = Column("alpha_dwn_std_dev", Double, nullable=True)
    alpha_mean = Column("alpha_mean", Double, nullable=True)
    alpha_median = Column("alpha_median", Double, nullable=True)
    alpha_sharpe = Column("alpha_sharpe", Double, nullable=True)
    alpha_std = Column("alpha_std", Double, nullable=True)
    avg_n_stck = Column("avg_n_stck", Double, nullable=True)
    dwn_std_dev = Column("dwn_std_dev", Double, nullable=True)
    highest_alpha = Column("highest_alpha", Double, nullable=True)
    highest_index = Column("highest_index", Double, nullable=True)
    highest_pcagr = Column("highest_pcagr", Double, nullable=True)
    index_mean = Column("index_mean", Double, nullable=True)
    index_median = Column("index_median", Double, nullable=True)
    index_sharpe = Column("index_sharpe", Double, nullable=True)
    index_std = Column("index_std", Double, nullable=True)
    indx_dwn_std_dev = Column("index_dwn_std_dev", Double, nullable=True)  # Note: database has index_dwn_std_dev
    insert_time = Column("insert_time", Text, nullable=True)
    lowest_alpha = Column("lowest_alpha", Double, nullable=True)
    lowest_index = Column("lowest_index", Double, nullable=True)
    lowest_pcagr = Column("lowest_pcagr", Double, nullable=True)
    mean = Column("mean", Double, nullable=True)
    median = Column("median", Double, nullable=True)
    mod_list_pct = Column("Mod_List%", Text, nullable=True)
    ndatapoints = Column("ndatapoints", Integer, nullable=True)  # Database has ndatapoint, not ndatapoints
    nyears = Column("nyears", Integer, nullable=True)
    prob_0 = Column("prob_0", Double, nullable=True)
    prob_0_07 = Column("prob_0.07", Double, nullable=True)
    prob_0_15 = Column("prob_0.15", Double, nullable=True)
    prob_0_15_pos = Column("prob_0.15_pos", Double, nullable=True)
    prob_0_25 = Column("prob_0.25", Double, nullable=True)
    prob_0_5 = Column("prob_0.5", Double, nullable=True)
    prob_1 = Column("prob_1", Double, nullable=True)
    reference_file = Column("reference_file", Text, nullable=True)
    sharpe = Column("sharpe", Double, nullable=True)
    std = Column("std", Double, nullable=True)
    strat_name = Column("strat_name", Text, nullable=True)
    strat_uuid = Column("strat_uuid", Text, nullable=True)
    tag = Column("tag", Text, nullable=True)

class CalYear(Base):
    __tablename__ = "cal_year"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Text, nullable=True)
    user_id = Column(Text, nullable=True)
    year = Column(Integer, nullable=True)
    portfolio_cagr = Column(Double, nullable=True)
    index_cagr = Column(Double, nullable=True)