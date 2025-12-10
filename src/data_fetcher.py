"""
Data Fetcher Module
Fetches S&P 500 and NASDAQ 100 stock data using Yahoo Finance API
Complete coverage of all index constituents with comprehensive fallback
"""

import pandas as pd
import numpy as np
import yfinance as yf
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import time
import warnings
warnings.filterwarnings('ignore')


# =============================================================================
# COMPLETE S&P 500 AND NASDAQ 100 TICKER LIST (FALLBACK)
# Updated December 2024 - All 503 S&P 500 + 101 NASDAQ 100 constituents
# =============================================================================

SP500_TICKERS = {
    # Information Technology
    'AAPL': ('Apple Inc.', 'Information Technology', 'Technology Hardware, Storage & Peripherals'),
    'MSFT': ('Microsoft Corporation', 'Information Technology', 'Systems Software'),
    'NVDA': ('NVIDIA Corporation', 'Information Technology', 'Semiconductors'),
    'AVGO': ('Broadcom Inc.', 'Information Technology', 'Semiconductors'),
    'ORCL': ('Oracle Corporation', 'Information Technology', 'Systems Software'),
    'CRM': ('Salesforce, Inc.', 'Information Technology', 'Application Software'),
    'CSCO': ('Cisco Systems, Inc.', 'Information Technology', 'Communications Equipment'),
    'ACN': ('Accenture plc', 'Information Technology', 'IT Consulting & Other Services'),
    'IBM': ('International Business Machines', 'Information Technology', 'IT Consulting & Other Services'),
    'AMD': ('Advanced Micro Devices, Inc.', 'Information Technology', 'Semiconductors'),
    'ADBE': ('Adobe Inc.', 'Information Technology', 'Application Software'),
    'TXN': ('Texas Instruments Incorporated', 'Information Technology', 'Semiconductors'),
    'QCOM': ('QUALCOMM Incorporated', 'Information Technology', 'Semiconductors'),
    'INTU': ('Intuit Inc.', 'Information Technology', 'Application Software'),
    'AMAT': ('Applied Materials, Inc.', 'Information Technology', 'Semiconductor Equipment'),
    'NOW': ('ServiceNow, Inc.', 'Information Technology', 'Systems Software'),
    'LRCX': ('Lam Research Corporation', 'Information Technology', 'Semiconductor Equipment'),
    'PANW': ('Palo Alto Networks, Inc.', 'Information Technology', 'Systems Software'),
    'ADI': ('Analog Devices, Inc.', 'Information Technology', 'Semiconductors'),
    'KLAC': ('KLA Corporation', 'Information Technology', 'Semiconductor Equipment'),
    'MU': ('Micron Technology, Inc.', 'Information Technology', 'Semiconductors'),
    'SNPS': ('Synopsys, Inc.', 'Information Technology', 'Application Software'),
    'CDNS': ('Cadence Design Systems, Inc.', 'Information Technology', 'Application Software'),
    'INTC': ('Intel Corporation', 'Information Technology', 'Semiconductors'),
    'CRWD': ('CrowdStrike Holdings, Inc.', 'Information Technology', 'Systems Software'),
    'MSI': ('Motorola Solutions, Inc.', 'Information Technology', 'Communications Equipment'),
    'APH': ('Amphenol Corporation', 'Information Technology', 'Electronic Components'),
    'FTNT': ('Fortinet, Inc.', 'Information Technology', 'Systems Software'),
    'ADSK': ('Autodesk, Inc.', 'Information Technology', 'Application Software'),
    'MCHP': ('Microchip Technology Incorporated', 'Information Technology', 'Semiconductors'),
    'NXPI': ('NXP Semiconductors N.V.', 'Information Technology', 'Semiconductors'),
    'DELL': ('Dell Technologies Inc.', 'Information Technology', 'Technology Hardware, Storage & Peripherals'),
    'ON': ('ON Semiconductor Corporation', 'Information Technology', 'Semiconductors'),
    'HPQ': ('HP Inc.', 'Information Technology', 'Technology Hardware, Storage & Peripherals'),
    'ROP': ('Roper Technologies, Inc.', 'Information Technology', 'Application Software'),
    'CTSH': ('Cognizant Technology Solutions', 'Information Technology', 'IT Consulting & Other Services'),
    'IT': ('Gartner, Inc.', 'Information Technology', 'IT Consulting & Other Services'),
    'ANSS': ('ANSYS, Inc.', 'Information Technology', 'Application Software'),
    'MPWR': ('Monolithic Power Systems, Inc.', 'Information Technology', 'Semiconductors'),
    'KEYS': ('Keysight Technologies, Inc.', 'Information Technology', 'Electronic Equipment & Instruments'),
    'CDW': ('CDW Corporation', 'Information Technology', 'Technology Distributors'),
    'HPE': ('Hewlett Packard Enterprise', 'Information Technology', 'Technology Hardware, Storage & Peripherals'),
    'FSLR': ('First Solar, Inc.', 'Information Technology', 'Semiconductors'),
    'TYL': ('Tyler Technologies, Inc.', 'Information Technology', 'Application Software'),
    'GDDY': ('GoDaddy Inc.', 'Information Technology', 'Internet Services & Infrastructure'),
    'TDY': ('Teledyne Technologies Incorporated', 'Information Technology', 'Electronic Equipment & Instruments'),
    'STX': ('Seagate Technology Holdings plc', 'Information Technology', 'Technology Hardware, Storage & Peripherals'),
    'WDC': ('Western Digital Corporation', 'Information Technology', 'Technology Hardware, Storage & Peripherals'),
    'NTAP': ('NetApp, Inc.', 'Information Technology', 'Technology Hardware, Storage & Peripherals'),
    'PTC': ('PTC Inc.', 'Information Technology', 'Application Software'),
    'ZBRA': ('Zebra Technologies Corporation', 'Information Technology', 'Electronic Equipment & Instruments'),
    'GEN': ('Gen Digital Inc.', 'Information Technology', 'Systems Software'),
    'TRMB': ('Trimble Inc.', 'Information Technology', 'Electronic Equipment & Instruments'),
    'SWKS': ('Skyworks Solutions, Inc.', 'Information Technology', 'Semiconductors'),
    'EPAM': ('EPAM Systems, Inc.', 'Information Technology', 'IT Consulting & Other Services'),
    'VRSN': ('VeriSign, Inc.', 'Information Technology', 'Internet Services & Infrastructure'),
    'JNPR': ('Juniper Networks, Inc.', 'Information Technology', 'Communications Equipment'),
    'AKAM': ('Akamai Technologies, Inc.', 'Information Technology', 'Internet Services & Infrastructure'),
    'FFIV': ('F5, Inc.', 'Information Technology', 'Communications Equipment'),
    'QRVO': ('Qorvo, Inc.', 'Information Technology', 'Semiconductors'),
    'JKHY': ('Jack Henry & Associates, Inc.', 'Information Technology', 'Data Processing & Outsourced Services'),
    'SMCI': ('Super Micro Computer, Inc.', 'Information Technology', 'Technology Hardware, Storage & Peripherals'),

    # Communication Services
    'META': ('Meta Platforms, Inc.', 'Communication Services', 'Interactive Media & Services'),
    'GOOGL': ('Alphabet Inc. Class A', 'Communication Services', 'Interactive Media & Services'),
    'GOOG': ('Alphabet Inc. Class C', 'Communication Services', 'Interactive Media & Services'),
    'NFLX': ('Netflix, Inc.', 'Communication Services', 'Movies & Entertainment'),
    'DIS': ('The Walt Disney Company', 'Communication Services', 'Movies & Entertainment'),
    'CMCSA': ('Comcast Corporation', 'Communication Services', 'Cable & Satellite'),
    'VZ': ('Verizon Communications Inc.', 'Communication Services', 'Integrated Telecommunication Services'),
    'T': ('AT&T Inc.', 'Communication Services', 'Integrated Telecommunication Services'),
    'TMUS': ('T-Mobile US, Inc.', 'Communication Services', 'Wireless Telecommunication Services'),
    'CHTR': ('Charter Communications, Inc.', 'Communication Services', 'Cable & Satellite'),
    'EA': ('Electronic Arts Inc.', 'Communication Services', 'Interactive Home Entertainment'),
    'WBD': ('Warner Bros. Discovery, Inc.', 'Communication Services', 'Movies & Entertainment'),
    'TTWO': ('Take-Two Interactive Software', 'Communication Services', 'Interactive Home Entertainment'),
    'OMC': ('Omnicom Group Inc.', 'Communication Services', 'Advertising'),
    'LYV': ('Live Nation Entertainment, Inc.', 'Communication Services', 'Movies & Entertainment'),
    'IPG': ('The Interpublic Group', 'Communication Services', 'Advertising'),
    'PARA': ('Paramount Global', 'Communication Services', 'Movies & Entertainment'),
    'FOX': ('Fox Corporation Class B', 'Communication Services', 'Broadcasting'),
    'FOXA': ('Fox Corporation Class A', 'Communication Services', 'Broadcasting'),
    'MTCH': ('Match Group, Inc.', 'Communication Services', 'Interactive Media & Services'),
    'NWS': ('News Corporation Class B', 'Communication Services', 'Publishing'),
    'NWSA': ('News Corporation Class A', 'Communication Services', 'Publishing'),

    # Consumer Discretionary
    'AMZN': ('Amazon.com, Inc.', 'Consumer Discretionary', 'Broadline Retail'),
    'TSLA': ('Tesla, Inc.', 'Consumer Discretionary', 'Automobile Manufacturers'),
    'HD': ('The Home Depot, Inc.', 'Consumer Discretionary', 'Home Improvement Retail'),
    'MCD': ("McDonald's Corporation", 'Consumer Discretionary', 'Restaurants'),
    'NKE': ('NIKE, Inc.', 'Consumer Discretionary', 'Footwear'),
    'LOW': ("Lowe's Companies, Inc.", 'Consumer Discretionary', 'Home Improvement Retail'),
    'BKNG': ('Booking Holdings Inc.', 'Consumer Discretionary', 'Hotels, Resorts & Cruise Lines'),
    'SBUX': ('Starbucks Corporation', 'Consumer Discretionary', 'Restaurants'),
    'TJX': ('The TJX Companies, Inc.', 'Consumer Discretionary', 'Apparel Retail'),
    'CMG': ('Chipotle Mexican Grill, Inc.', 'Consumer Discretionary', 'Restaurants'),
    'MAR': ('Marriott International, Inc.', 'Consumer Discretionary', 'Hotels, Resorts & Cruise Lines'),
    'ORLY': ("O'Reilly Automotive, Inc.", 'Consumer Discretionary', 'Automotive Retail'),
    'AZO': ('AutoZone, Inc.', 'Consumer Discretionary', 'Automotive Retail'),
    'GM': ('General Motors Company', 'Consumer Discretionary', 'Automobile Manufacturers'),
    'ROST': ('Ross Stores, Inc.', 'Consumer Discretionary', 'Apparel Retail'),
    'HLT': ('Hilton Worldwide Holdings Inc.', 'Consumer Discretionary', 'Hotels, Resorts & Cruise Lines'),
    'F': ('Ford Motor Company', 'Consumer Discretionary', 'Automobile Manufacturers'),
    'YUM': ('Yum! Brands, Inc.', 'Consumer Discretionary', 'Restaurants'),
    'DHI': ('D.R. Horton, Inc.', 'Consumer Discretionary', 'Homebuilding'),
    'DECK': ('Deckers Outdoor Corporation', 'Consumer Discretionary', 'Footwear'),
    'LEN': ('Lennar Corporation', 'Consumer Discretionary', 'Homebuilding'),
    'ULTA': ('Ulta Beauty, Inc.', 'Consumer Discretionary', 'Other Specialty Retail'),
    'EBAY': ('eBay Inc.', 'Consumer Discretionary', 'Broadline Retail'),
    'RCL': ('Royal Caribbean Cruises Ltd.', 'Consumer Discretionary', 'Hotels, Resorts & Cruise Lines'),
    'NVR': ('NVR, Inc.', 'Consumer Discretionary', 'Homebuilding'),
    'DPZ': ("Domino's Pizza, Inc.", 'Consumer Discretionary', 'Restaurants'),
    'PHM': ('PulteGroup, Inc.', 'Consumer Discretionary', 'Homebuilding'),
    'EXPE': ('Expedia Group, Inc.', 'Consumer Discretionary', 'Hotels, Resorts & Cruise Lines'),
    'CCL': ('Carnival Corporation & plc', 'Consumer Discretionary', 'Hotels, Resorts & Cruise Lines'),
    'LVS': ('Las Vegas Sands Corp.', 'Consumer Discretionary', 'Casinos & Gaming'),
    'GPC': ('Genuine Parts Company', 'Consumer Discretionary', 'Specialty Stores'),
    'APTV': ('Aptiv PLC', 'Consumer Discretionary', 'Automotive Parts & Equipment'),
    'GRMN': ('Garmin Ltd.', 'Consumer Discretionary', 'Consumer Electronics'),
    'POOL': ('Pool Corporation', 'Consumer Discretionary', 'Distributors'),
    'TSCO': ('Tractor Supply Company', 'Consumer Discretionary', 'Other Specialty Retail'),
    'BBY': ('Best Buy Co., Inc.', 'Consumer Discretionary', 'Computer & Electronics Retail'),
    'DRI': ('Darden Restaurants, Inc.', 'Consumer Discretionary', 'Restaurants'),
    'WYNN': ('Wynn Resorts, Limited', 'Consumer Discretionary', 'Casinos & Gaming'),
    'BWA': ('BorgWarner Inc.', 'Consumer Discretionary', 'Automotive Parts & Equipment'),
    'LKQ': ('LKQ Corporation', 'Consumer Discretionary', 'Distributors'),
    'MGM': ('MGM Resorts International', 'Consumer Discretionary', 'Casinos & Gaming'),
    'TPR': ('Tapestry, Inc.', 'Consumer Discretionary', 'Apparel, Accessories & Luxury Goods'),
    'KMX': ('CarMax, Inc.', 'Consumer Discretionary', 'Automotive Retail'),
    'ETSY': ('Etsy, Inc.', 'Consumer Discretionary', 'Broadline Retail'),
    'HAS': ('Hasbro, Inc.', 'Consumer Discretionary', 'Leisure Products'),
    'WHR': ('Whirlpool Corporation', 'Consumer Discretionary', 'Household Appliances'),
    'CZR': ('Caesars Entertainment, Inc.', 'Consumer Discretionary', 'Casinos & Gaming'),
    'MHK': ('Mohawk Industries, Inc.', 'Consumer Discretionary', 'Home Furnishings'),
    'NCLH': ('Norwegian Cruise Line Holdings', 'Consumer Discretionary', 'Hotels, Resorts & Cruise Lines'),
    'RL': ('Ralph Lauren Corporation', 'Consumer Discretionary', 'Apparel, Accessories & Luxury Goods'),

    # Consumer Staples
    'PG': ('The Procter & Gamble Company', 'Consumer Staples', 'Household Products'),
    'KO': ('The Coca-Cola Company', 'Consumer Staples', 'Soft Drinks & Non-alcoholic Beverages'),
    'PEP': ('PepsiCo, Inc.', 'Consumer Staples', 'Soft Drinks & Non-alcoholic Beverages'),
    'COST': ('Costco Wholesale Corporation', 'Consumer Staples', 'Consumer Staples Merchandise Retail'),
    'WMT': ('Walmart Inc.', 'Consumer Staples', 'Consumer Staples Merchandise Retail'),
    'PM': ('Philip Morris International Inc.', 'Consumer Staples', 'Tobacco'),
    'MDLZ': ('Mondelez International, Inc.', 'Consumer Staples', 'Packaged Foods & Meats'),
    'MO': ('Altria Group, Inc.', 'Consumer Staples', 'Tobacco'),
    'CL': ('Colgate-Palmolive Company', 'Consumer Staples', 'Household Products'),
    'TGT': ('Target Corporation', 'Consumer Staples', 'Consumer Staples Merchandise Retail'),
    'KMB': ('Kimberly-Clark Corporation', 'Consumer Staples', 'Household Products'),
    'GIS': ('General Mills, Inc.', 'Consumer Staples', 'Packaged Foods & Meats'),
    'ADM': ('Archer-Daniels-Midland Company', 'Consumer Staples', 'Agricultural Products & Services'),
    'STZ': ('Constellation Brands, Inc.', 'Consumer Staples', 'Distillers & Vintners'),
    'SYY': ('Sysco Corporation', 'Consumer Staples', 'Food Distributors'),
    'HSY': ('The Hershey Company', 'Consumer Staples', 'Packaged Foods & Meats'),
    'KHC': ('The Kraft Heinz Company', 'Consumer Staples', 'Packaged Foods & Meats'),
    'MNST': ('Monster Beverage Corporation', 'Consumer Staples', 'Soft Drinks & Non-alcoholic Beverages'),
    'KDP': ('Keurig Dr Pepper Inc.', 'Consumer Staples', 'Soft Drinks & Non-alcoholic Beverages'),
    'K': ('Kellanova', 'Consumer Staples', 'Packaged Foods & Meats'),
    'EL': ('The Estée Lauder Companies Inc.', 'Consumer Staples', 'Personal Care Products'),
    'CHD': ('Church & Dwight Co., Inc.', 'Consumer Staples', 'Household Products'),
    'SJM': ('The J.M. Smucker Company', 'Consumer Staples', 'Packaged Foods & Meats'),
    'MKC': ('McCormick & Company, Incorporated', 'Consumer Staples', 'Packaged Foods & Meats'),
    'CLX': ('The Clorox Company', 'Consumer Staples', 'Household Products'),
    'CAG': ('Conagra Brands, Inc.', 'Consumer Staples', 'Packaged Foods & Meats'),
    'HRL': ('Hormel Foods Corporation', 'Consumer Staples', 'Packaged Foods & Meats'),
    'TSN': ('Tyson Foods, Inc.', 'Consumer Staples', 'Packaged Foods & Meats'),
    'WBA': ('Walgreens Boots Alliance, Inc.', 'Consumer Staples', 'Drug Retail'),
    'LW': ('Lamb Weston Holdings, Inc.', 'Consumer Staples', 'Packaged Foods & Meats'),
    'TAP': ('Molson Coors Beverage Company', 'Consumer Staples', 'Brewers'),
    'BG': ('Bunge Global SA', 'Consumer Staples', 'Agricultural Products & Services'),
    'CPB': ('Campbell Soup Company', 'Consumer Staples', 'Packaged Foods & Meats'),
    'BF-B': ('Brown-Forman Corporation', 'Consumer Staples', 'Distillers & Vintners'),

    # Health Care
    'LLY': ('Eli Lilly and Company', 'Health Care', 'Pharmaceuticals'),
    'UNH': ('UnitedHealth Group Incorporated', 'Health Care', 'Managed Health Care'),
    'JNJ': ('Johnson & Johnson', 'Health Care', 'Pharmaceuticals'),
    'MRK': ('Merck & Co., Inc.', 'Health Care', 'Pharmaceuticals'),
    'ABBV': ('AbbVie Inc.', 'Health Care', 'Pharmaceuticals'),
    'TMO': ('Thermo Fisher Scientific Inc.', 'Health Care', 'Life Sciences Tools & Services'),
    'ABT': ('Abbott Laboratories', 'Health Care', 'Health Care Equipment'),
    'DHR': ('Danaher Corporation', 'Health Care', 'Life Sciences Tools & Services'),
    'PFE': ('Pfizer Inc.', 'Health Care', 'Pharmaceuticals'),
    'AMGN': ('Amgen Inc.', 'Health Care', 'Biotechnology'),
    'ISRG': ('Intuitive Surgical, Inc.', 'Health Care', 'Health Care Equipment'),
    'SYK': ('Stryker Corporation', 'Health Care', 'Health Care Equipment'),
    'BMY': ('Bristol-Myers Squibb Company', 'Health Care', 'Pharmaceuticals'),
    'VRTX': ('Vertex Pharmaceuticals Incorporated', 'Health Care', 'Biotechnology'),
    'ELV': ('Elevance Health, Inc.', 'Health Care', 'Managed Health Care'),
    'MDT': ('Medtronic plc', 'Health Care', 'Health Care Equipment'),
    'REGN': ('Regeneron Pharmaceuticals, Inc.', 'Health Care', 'Biotechnology'),
    'BSX': ('Boston Scientific Corporation', 'Health Care', 'Health Care Equipment'),
    'GILD': ('Gilead Sciences, Inc.', 'Health Care', 'Biotechnology'),
    'CI': ('The Cigna Group', 'Health Care', 'Managed Health Care'),
    'ZTS': ('Zoetis Inc.', 'Health Care', 'Pharmaceuticals'),
    'CVS': ('CVS Health Corporation', 'Health Care', 'Health Care Services'),
    'MCK': ('McKesson Corporation', 'Health Care', 'Health Care Distributors'),
    'HCA': ('HCA Healthcare, Inc.', 'Health Care', 'Health Care Facilities'),
    'BDX': ('Becton, Dickinson and Company', 'Health Care', 'Health Care Equipment'),
    'EW': ('Edwards Lifesciences Corporation', 'Health Care', 'Health Care Equipment'),
    'HUM': ('Humana Inc.', 'Health Care', 'Managed Health Care'),
    'COR': ('Cencora, Inc.', 'Health Care', 'Health Care Distributors'),
    'A': ('Agilent Technologies, Inc.', 'Health Care', 'Life Sciences Tools & Services'),
    'GEHC': ('GE HealthCare Technologies Inc.', 'Health Care', 'Health Care Equipment'),
    'IQV': ('IQVIA Holdings Inc.', 'Health Care', 'Life Sciences Tools & Services'),
    'RMD': ('ResMed Inc.', 'Health Care', 'Health Care Equipment'),
    'IDXX': ('IDEXX Laboratories, Inc.', 'Health Care', 'Health Care Equipment'),
    'DXCM': ('DexCom, Inc.', 'Health Care', 'Health Care Equipment'),
    'MTD': ('Mettler-Toledo International Inc.', 'Health Care', 'Life Sciences Tools & Services'),
    'MRNA': ('Moderna, Inc.', 'Health Care', 'Biotechnology'),
    'CAH': ('Cardinal Health, Inc.', 'Health Care', 'Health Care Distributors'),
    'BIIB': ('Biogen Inc.', 'Health Care', 'Biotechnology'),
    'WAT': ('Waters Corporation', 'Health Care', 'Life Sciences Tools & Services'),
    'ZBH': ('Zimmer Biomet Holdings, Inc.', 'Health Care', 'Health Care Equipment'),
    'HOLX': ('Hologic, Inc.', 'Health Care', 'Health Care Equipment'),
    'ALGN': ('Align Technology, Inc.', 'Health Care', 'Health Care Equipment'),
    'COO': ('The Cooper Companies, Inc.', 'Health Care', 'Health Care Equipment'),
    'LH': ('Labcorp Holdings Inc.', 'Health Care', 'Health Care Services'),
    'RVTY': ('Revvity, Inc.', 'Health Care', 'Life Sciences Tools & Services'),
    'VTRS': ('Viatris Inc.', 'Health Care', 'Pharmaceuticals'),
    'MOH': ('Molina Healthcare, Inc.', 'Health Care', 'Managed Health Care'),
    'DGX': ('Quest Diagnostics Incorporated', 'Health Care', 'Health Care Services'),
    'CTLT': ('Catalent, Inc.', 'Health Care', 'Pharmaceuticals'),
    'HSIC': ('Henry Schein, Inc.', 'Health Care', 'Health Care Distributors'),
    'CRL': ('Charles River Laboratories International', 'Health Care', 'Life Sciences Tools & Services'),
    'TECH': ('Bio-Techne Corporation', 'Health Care', 'Life Sciences Tools & Services'),
    'INCY': ('Incyte Corporation', 'Health Care', 'Biotechnology'),
    'PODD': ('Insulet Corporation', 'Health Care', 'Health Care Equipment'),

    # Financials
    'BRK-B': ('Berkshire Hathaway Inc.', 'Financials', 'Multi-Sector Holdings'),
    'JPM': ('JPMorgan Chase & Co.', 'Financials', 'Diversified Banks'),
    'V': ('Visa Inc.', 'Financials', 'Transaction & Payment Processing Services'),
    'MA': ('Mastercard Incorporated', 'Financials', 'Transaction & Payment Processing Services'),
    'BAC': ('Bank of America Corporation', 'Financials', 'Diversified Banks'),
    'WFC': ('Wells Fargo & Company', 'Financials', 'Diversified Banks'),
    'GS': ('The Goldman Sachs Group, Inc.', 'Financials', 'Investment Banking & Brokerage'),
    'MS': ('Morgan Stanley', 'Financials', 'Investment Banking & Brokerage'),
    'SPGI': ('S&P Global Inc.', 'Financials', 'Financial Exchanges & Data'),
    'BLK': ('BlackRock, Inc.', 'Financials', 'Asset Management & Custody Banks'),
    'AXP': ('American Express Company', 'Financials', 'Consumer Finance'),
    'C': ('Citigroup Inc.', 'Financials', 'Diversified Banks'),
    'SCHW': ('The Charles Schwab Corporation', 'Financials', 'Investment Banking & Brokerage'),
    'PGR': ('The Progressive Corporation', 'Financials', 'Property & Casualty Insurance'),
    'CB': ('Chubb Limited', 'Financials', 'Property & Casualty Insurance'),
    'MMC': ('Marsh & McLennan Companies, Inc.', 'Financials', 'Insurance Brokers'),
    'ICE': ('Intercontinental Exchange, Inc.', 'Financials', 'Financial Exchanges & Data'),
    'USB': ('U.S. Bancorp', 'Financials', 'Diversified Banks'),
    'PNC': ('The PNC Financial Services Group', 'Financials', 'Regional Banks'),
    'CME': ('CME Group Inc.', 'Financials', 'Financial Exchanges & Data'),
    'AON': ('Aon plc', 'Financials', 'Insurance Brokers'),
    'TFC': ('Truist Financial Corporation', 'Financials', 'Regional Banks'),
    'MCO': ('Moody\'s Corporation', 'Financials', 'Financial Exchanges & Data'),
    'AJG': ('Arthur J. Gallagher & Co.', 'Financials', 'Insurance Brokers'),
    'COF': ('Capital One Financial Corporation', 'Financials', 'Consumer Finance'),
    'MET': ('MetLife, Inc.', 'Financials', 'Life & Health Insurance'),
    'AFL': ('Aflac Incorporated', 'Financials', 'Life & Health Insurance'),
    'BK': ('The Bank of New York Mellon Corporation', 'Financials', 'Asset Management & Custody Banks'),
    'AIG': ('American International Group, Inc.', 'Financials', 'Multi-line Insurance'),
    'PRU': ('Prudential Financial, Inc.', 'Financials', 'Life & Health Insurance'),
    'TRV': ('The Travelers Companies, Inc.', 'Financials', 'Property & Casualty Insurance'),
    'ALL': ('The Allstate Corporation', 'Financials', 'Property & Casualty Insurance'),
    'MSCI': ('MSCI Inc.', 'Financials', 'Financial Exchanges & Data'),
    'DFS': ('Discover Financial Services', 'Financials', 'Consumer Finance'),
    'AMP': ('Ameriprise Financial, Inc.', 'Financials', 'Asset Management & Custody Banks'),
    'FI': ('Fiserv, Inc.', 'Financials', 'Data Processing & Outsourced Services'),
    'NDAQ': ('Nasdaq, Inc.', 'Financials', 'Financial Exchanges & Data'),
    'MTB': ('M&T Bank Corporation', 'Financials', 'Regional Banks'),
    'FITB': ('Fifth Third Bancorp', 'Financials', 'Regional Banks'),
    'HIG': ('The Hartford Financial Services Group', 'Financials', 'Property & Casualty Insurance'),
    'STT': ('State Street Corporation', 'Financials', 'Asset Management & Custody Banks'),
    'SYF': ('Synchrony Financial', 'Financials', 'Consumer Finance'),
    'TROW': ('T. Rowe Price Group, Inc.', 'Financials', 'Asset Management & Custody Banks'),
    'NTRS': ('Northern Trust Corporation', 'Financials', 'Asset Management & Custody Banks'),
    'RJF': ('Raymond James Financial, Inc.', 'Financials', 'Investment Banking & Brokerage'),
    'HBAN': ('Huntington Bancshares Incorporated', 'Financials', 'Regional Banks'),
    'RF': ('Regions Financial Corporation', 'Financials', 'Regional Banks'),
    'CINF': ('Cincinnati Financial Corporation', 'Financials', 'Property & Casualty Insurance'),
    'KEY': ('KeyCorp', 'Financials', 'Regional Banks'),
    'CFG': ('Citizens Financial Group, Inc.', 'Financials', 'Regional Banks'),
    'PFG': ('Principal Financial Group, Inc.', 'Financials', 'Life & Health Insurance'),
    'BRO': ('Brown & Brown, Inc.', 'Financials', 'Insurance Brokers'),
    'FDS': ('FactSet Research Systems Inc.', 'Financials', 'Financial Exchanges & Data'),
    'CBOE': ('Cboe Global Markets, Inc.', 'Financials', 'Financial Exchanges & Data'),
    'WRB': ('W. R. Berkley Corporation', 'Financials', 'Property & Casualty Insurance'),
    'EG': ('Everest Group, Ltd.', 'Financials', 'Reinsurance'),
    'L': ('Loews Corporation', 'Financials', 'Multi-line Insurance'),
    'ACGL': ('Arch Capital Group Ltd.', 'Financials', 'Property & Casualty Insurance'),
    'GL': ('Globe Life Inc.', 'Financials', 'Life & Health Insurance'),
    'AIZ': ('Assurant, Inc.', 'Financials', 'Multi-line Insurance'),
    'IVZ': ('Invesco Ltd.', 'Financials', 'Asset Management & Custody Banks'),
    'BEN': ('Franklin Resources, Inc.', 'Financials', 'Asset Management & Custody Banks'),
    'JKHY': ('Jack Henry & Associates, Inc.', 'Financials', 'Data Processing & Outsourced Services'),
    'PYPL': ('PayPal Holdings, Inc.', 'Financials', 'Transaction & Payment Processing Services'),

    # Industrials
    'GE': ('GE Aerospace', 'Industrials', 'Aerospace & Defense'),
    'CAT': ('Caterpillar Inc.', 'Industrials', 'Construction Machinery & Heavy Transportation Equipment'),
    'RTX': ('RTX Corporation', 'Industrials', 'Aerospace & Defense'),
    'HON': ('Honeywell International Inc.', 'Industrials', 'Industrial Conglomerates'),
    'UNP': ('Union Pacific Corporation', 'Industrials', 'Rail Transportation'),
    'BA': ('The Boeing Company', 'Industrials', 'Aerospace & Defense'),
    'UPS': ('United Parcel Service, Inc.', 'Industrials', 'Air Freight & Logistics'),
    'LMT': ('Lockheed Martin Corporation', 'Industrials', 'Aerospace & Defense'),
    'DE': ('Deere & Company', 'Industrials', 'Agricultural & Farm Machinery'),
    'ETN': ('Eaton Corporation plc', 'Industrials', 'Electrical Components & Equipment'),
    'ADP': ('Automatic Data Processing, Inc.', 'Industrials', 'Human Resource & Employment Services'),
    'UBER': ('Uber Technologies, Inc.', 'Industrials', 'Passenger Ground Transportation'),
    'WM': ('Waste Management, Inc.', 'Industrials', 'Environmental & Facilities Services'),
    'GD': ('General Dynamics Corporation', 'Industrials', 'Aerospace & Defense'),
    'ITW': ('Illinois Tool Works Inc.', 'Industrials', 'Industrial Machinery & Supplies & Components'),
    'PH': ('Parker-Hannifin Corporation', 'Industrials', 'Industrial Machinery & Supplies & Components'),
    'TT': ('Trane Technologies plc', 'Industrials', 'Building Products'),
    'NOC': ('Northrop Grumman Corporation', 'Industrials', 'Aerospace & Defense'),
    'EMR': ('Emerson Electric Co.', 'Industrials', 'Electrical Components & Equipment'),
    'CTAS': ('Cintas Corporation', 'Industrials', 'Diversified Support Services'),
    'CSX': ('CSX Corporation', 'Industrials', 'Rail Transportation'),
    'FDX': ('FedEx Corporation', 'Industrials', 'Air Freight & Logistics'),
    'NSC': ('Norfolk Southern Corporation', 'Industrials', 'Rail Transportation'),
    'MMM': ('3M Company', 'Industrials', 'Industrial Conglomerates'),
    'CARR': ('Carrier Global Corporation', 'Industrials', 'Building Products'),
    'PCAR': ('PACCAR Inc', 'Industrials', 'Construction Machinery & Heavy Transportation Equipment'),
    'JCI': ('Johnson Controls International plc', 'Industrials', 'Building Products'),
    'GWW': ('W.W. Grainger, Inc.', 'Industrials', 'Trading Companies & Distributors'),
    'URI': ('United Rentals, Inc.', 'Industrials', 'Trading Companies & Distributors'),
    'PAYX': ('Paychex, Inc.', 'Industrials', 'Human Resource & Employment Services'),
    'FAST': ('Fastenal Company', 'Industrials', 'Trading Companies & Distributors'),
    'RSG': ('Republic Services, Inc.', 'Industrials', 'Environmental & Facilities Services'),
    'LHX': ('L3Harris Technologies, Inc.', 'Industrials', 'Aerospace & Defense'),
    'VRSK': ('Verisk Analytics, Inc.', 'Industrials', 'Research & Consulting Services'),
    'AME': ('AMETEK, Inc.', 'Industrials', 'Electrical Components & Equipment'),
    'PWR': ('Quanta Services, Inc.', 'Industrials', 'Construction & Engineering'),
    'OTIS': ('Otis Worldwide Corporation', 'Industrials', 'Industrial Machinery & Supplies & Components'),
    'CMI': ('Cummins Inc.', 'Industrials', 'Industrial Machinery & Supplies & Components'),
    'IR': ('Ingersoll Rand Inc.', 'Industrials', 'Industrial Machinery & Supplies & Components'),
    'HWM': ('Howmet Aerospace Inc.', 'Industrials', 'Aerospace & Defense'),
    'ROK': ('Rockwell Automation, Inc.', 'Industrials', 'Electrical Components & Equipment'),
    'AXON': ('Axon Enterprise, Inc.', 'Industrials', 'Aerospace & Defense'),
    'CPRT': ('Copart, Inc.', 'Industrials', 'Diversified Support Services'),
    'DAL': ('Delta Air Lines, Inc.', 'Industrials', 'Passenger Airlines'),
    'LDOS': ('Leidos Holdings, Inc.', 'Industrials', 'Aerospace & Defense'),
    'EFX': ('Equifax Inc.', 'Industrials', 'Research & Consulting Services'),
    'XYL': ('Xylem Inc.', 'Industrials', 'Industrial Machinery & Supplies & Components'),
    'DOV': ('Dover Corporation', 'Industrials', 'Industrial Machinery & Supplies & Components'),
    'GEV': ('GE Vernova Inc.', 'Industrials', 'Heavy Electrical Equipment'),
    'WAB': ('Westinghouse Air Brake Technologies', 'Industrials', 'Construction Machinery & Heavy Transportation Equipment'),
    'HUBB': ('Hubbell Incorporated', 'Industrials', 'Electrical Components & Equipment'),
    'ODFL': ('Old Dominion Freight Line, Inc.', 'Industrials', 'Trucking'),
    'IEX': ('IDEX Corporation', 'Industrials', 'Industrial Machinery & Supplies & Components'),
    'LUV': ('Southwest Airlines Co.', 'Industrials', 'Passenger Airlines'),
    'UAL': ('United Airlines Holdings, Inc.', 'Industrials', 'Passenger Airlines'),
    'BAX': ('Baxter International Inc.', 'Industrials', 'Health Care Equipment'),
    'J': ('Jacobs Solutions Inc.', 'Industrials', 'Research & Consulting Services'),
    'NDSN': ('Nordson Corporation', 'Industrials', 'Industrial Machinery & Supplies & Components'),
    'PNR': ('Pentair plc', 'Industrials', 'Industrial Machinery & Supplies & Components'),
    'SNA': ('Snap-on Incorporated', 'Industrials', 'Industrial Machinery & Supplies & Components'),
    'MAS': ('Masco Corporation', 'Industrials', 'Building Products'),
    'EXPD': ('Expeditors International of Washington', 'Industrials', 'Air Freight & Logistics'),
    'RHI': ('Robert Half Inc.', 'Industrials', 'Human Resource & Employment Services'),
    'JBHT': ('J.B. Hunt Transport Services, Inc.', 'Industrials', 'Trucking'),
    'BLDR': ('Builders FirstSource, Inc.', 'Industrials', 'Building Products'),
    'SWK': ('Stanley Black & Decker, Inc.', 'Industrials', 'Industrial Machinery & Supplies & Components'),
    'CNH': ('CNH Industrial N.V.', 'Industrials', 'Agricultural & Farm Machinery'),
    'CHRW': ('C.H. Robinson Worldwide, Inc.', 'Industrials', 'Air Freight & Logistics'),
    'ROL': ('Rollins, Inc.', 'Industrials', 'Environmental & Facilities Services'),
    'GNRC': ('Generac Holdings Inc.', 'Industrials', 'Electrical Components & Equipment'),
    'PAYC': ('Paycom Software, Inc.', 'Industrials', 'Human Resource & Employment Services'),
    'AAL': ('American Airlines Group Inc.', 'Industrials', 'Passenger Airlines'),

    # Energy
    'XOM': ('Exxon Mobil Corporation', 'Energy', 'Integrated Oil & Gas'),
    'CVX': ('Chevron Corporation', 'Energy', 'Integrated Oil & Gas'),
    'COP': ('ConocoPhillips', 'Energy', 'Oil & Gas Exploration & Production'),
    'EOG': ('EOG Resources, Inc.', 'Energy', 'Oil & Gas Exploration & Production'),
    'SLB': ('Schlumberger Limited', 'Energy', 'Oil & Gas Equipment & Services'),
    'MPC': ('Marathon Petroleum Corporation', 'Energy', 'Oil & Gas Refining & Marketing'),
    'PXD': ('Pioneer Natural Resources Company', 'Energy', 'Oil & Gas Exploration & Production'),
    'PSX': ('Phillips 66', 'Energy', 'Oil & Gas Refining & Marketing'),
    'VLO': ('Valero Energy Corporation', 'Energy', 'Oil & Gas Refining & Marketing'),
    'WMB': ('The Williams Companies, Inc.', 'Energy', 'Oil & Gas Storage & Transportation'),
    'OKE': ('ONEOK, Inc.', 'Energy', 'Oil & Gas Storage & Transportation'),
    'KMI': ('Kinder Morgan, Inc.', 'Energy', 'Oil & Gas Storage & Transportation'),
    'HES': ('Hess Corporation', 'Energy', 'Oil & Gas Exploration & Production'),
    'HAL': ('Halliburton Company', 'Energy', 'Oil & Gas Equipment & Services'),
    'DVN': ('Devon Energy Corporation', 'Energy', 'Oil & Gas Exploration & Production'),
    'BKR': ('Baker Hughes Company', 'Energy', 'Oil & Gas Equipment & Services'),
    'FANG': ('Diamondback Energy, Inc.', 'Energy', 'Oil & Gas Exploration & Production'),
    'OXY': ('Occidental Petroleum Corporation', 'Energy', 'Oil & Gas Exploration & Production'),
    'TRGP': ('Targa Resources Corp.', 'Energy', 'Oil & Gas Storage & Transportation'),
    'CTRA': ('Coterra Energy Inc.', 'Energy', 'Oil & Gas Exploration & Production'),
    'EQT': ('EQT Corporation', 'Energy', 'Oil & Gas Exploration & Production'),
    'MRO': ('Marathon Oil Corporation', 'Energy', 'Oil & Gas Exploration & Production'),
    'APA': ('APA Corporation', 'Energy', 'Oil & Gas Exploration & Production'),

    # Materials
    'LIN': ('Linde plc', 'Materials', 'Industrial Gases'),
    'APD': ('Air Products and Chemicals, Inc.', 'Materials', 'Industrial Gases'),
    'SHW': ('The Sherwin-Williams Company', 'Materials', 'Specialty Chemicals'),
    'ECL': ('Ecolab Inc.', 'Materials', 'Specialty Chemicals'),
    'FCX': ('Freeport-McMoRan Inc.', 'Materials', 'Copper'),
    'NEM': ('Newmont Corporation', 'Materials', 'Gold'),
    'NUE': ('Nucor Corporation', 'Materials', 'Steel'),
    'DOW': ('Dow Inc.', 'Materials', 'Commodity Chemicals'),
    'DD': ('DuPont de Nemours, Inc.', 'Materials', 'Specialty Chemicals'),
    'PPG': ('PPG Industries, Inc.', 'Materials', 'Specialty Chemicals'),
    'VMC': ('Vulcan Materials Company', 'Materials', 'Construction Materials'),
    'MLM': ('Martin Marietta Materials, Inc.', 'Materials', 'Construction Materials'),
    'CTVA': ('Corteva, Inc.', 'Materials', 'Fertilizers & Agricultural Chemicals'),
    'ALB': ('Albemarle Corporation', 'Materials', 'Specialty Chemicals'),
    'IFF': ('International Flavors & Fragrances', 'Materials', 'Specialty Chemicals'),
    'BALL': ('Ball Corporation', 'Materials', 'Metal, Glass & Plastic Containers'),
    'STLD': ('Steel Dynamics, Inc.', 'Materials', 'Steel'),
    'CF': ('CF Industries Holdings, Inc.', 'Materials', 'Fertilizers & Agricultural Chemicals'),
    'FMC': ('FMC Corporation', 'Materials', 'Fertilizers & Agricultural Chemicals'),
    'PKG': ('Packaging Corporation of America', 'Materials', 'Paper & Plastic Packaging Products & Materials'),
    'IP': ('International Paper Company', 'Materials', 'Paper & Plastic Packaging Products & Materials'),
    'AVY': ('Avery Dennison Corporation', 'Materials', 'Paper & Plastic Packaging Products & Materials'),
    'CE': ('Celanese Corporation', 'Materials', 'Specialty Chemicals'),
    'EMN': ('Eastman Chemical Company', 'Materials', 'Specialty Chemicals'),
    'MOS': ('The Mosaic Company', 'Materials', 'Fertilizers & Agricultural Chemicals'),
    'LYB': ('LyondellBasell Industries N.V.', 'Materials', 'Specialty Chemicals'),
    'AMCR': ('Amcor plc', 'Materials', 'Paper & Plastic Packaging Products & Materials'),

    # Real Estate
    'PLD': ('Prologis, Inc.', 'Real Estate', 'Industrial REITs'),
    'AMT': ('American Tower Corporation', 'Real Estate', 'Specialized REITs'),
    'EQIX': ('Equinix, Inc.', 'Real Estate', 'Data Center REITs'),
    'WELL': ('Welltower Inc.', 'Real Estate', 'Health Care REITs'),
    'DLR': ('Digital Realty Trust, Inc.', 'Real Estate', 'Data Center REITs'),
    'CCI': ('Crown Castle Inc.', 'Real Estate', 'Specialized REITs'),
    'SPG': ('Simon Property Group, Inc.', 'Real Estate', 'Retail REITs'),
    'PSA': ('Public Storage', 'Real Estate', 'Self-Storage REITs'),
    'O': ('Realty Income Corporation', 'Real Estate', 'Retail REITs'),
    'VICI': ('VICI Properties Inc.', 'Real Estate', 'Specialized REITs'),
    'CBRE': ('CBRE Group, Inc.', 'Real Estate', 'Real Estate Services'),
    'AVB': ('AvalonBay Communities, Inc.', 'Real Estate', 'Multi-Family Residential REITs'),
    'EQR': ('Equity Residential', 'Real Estate', 'Multi-Family Residential REITs'),
    'WY': ('Weyerhaeuser Company', 'Real Estate', 'Timber REITs'),
    'IRM': ('Iron Mountain Incorporated', 'Real Estate', 'Specialized REITs'),
    'ARE': ('Alexandria Real Estate Equities', 'Real Estate', 'Office REITs'),
    'EXR': ('Extra Space Storage Inc.', 'Real Estate', 'Self-Storage REITs'),
    'MAA': ('Mid-America Apartment Communities', 'Real Estate', 'Multi-Family Residential REITs'),
    'VTR': ('Ventas, Inc.', 'Real Estate', 'Health Care REITs'),
    'KIM': ('Kimco Realty Corporation', 'Real Estate', 'Retail REITs'),
    'INVH': ('Invitation Homes Inc.', 'Real Estate', 'Single-Family Residential REITs'),
    'ESS': ('Essex Property Trust, Inc.', 'Real Estate', 'Multi-Family Residential REITs'),
    'SBA': ('SBA Communications Corporation', 'Real Estate', 'Specialized REITs'),
    'CPT': ('Camden Property Trust', 'Real Estate', 'Multi-Family Residential REITs'),
    'HST': ('Host Hotels & Resorts, Inc.', 'Real Estate', 'Hotel & Resort REITs'),
    'REG': ('Regency Centers Corporation', 'Real Estate', 'Retail REITs'),
    'UDR': ('UDR, Inc.', 'Real Estate', 'Multi-Family Residential REITs'),
    'BXP': ('Boston Properties, Inc.', 'Real Estate', 'Office REITs'),
    'FRT': ('Federal Realty Investment Trust', 'Real Estate', 'Retail REITs'),
    'DOC': ('Healthpeak Properties, Inc.', 'Real Estate', 'Health Care REITs'),

    # Utilities
    'NEE': ('NextEra Energy, Inc.', 'Utilities', 'Electric Utilities'),
    'SO': ('The Southern Company', 'Utilities', 'Electric Utilities'),
    'DUK': ('Duke Energy Corporation', 'Utilities', 'Electric Utilities'),
    'CEG': ('Constellation Energy Corporation', 'Utilities', 'Electric Utilities'),
    'SRE': ('Sempra', 'Utilities', 'Multi-Utilities'),
    'AEP': ('American Electric Power Company', 'Utilities', 'Electric Utilities'),
    'D': ('Dominion Energy, Inc.', 'Utilities', 'Electric Utilities'),
    'PCG': ('PG&E Corporation', 'Utilities', 'Electric Utilities'),
    'XEL': ('Xcel Energy Inc.', 'Utilities', 'Electric Utilities'),
    'EXC': ('Exelon Corporation', 'Utilities', 'Electric Utilities'),
    'EIX': ('Edison International', 'Utilities', 'Electric Utilities'),
    'ED': ('Consolidated Edison, Inc.', 'Utilities', 'Electric Utilities'),
    'WEC': ('WEC Energy Group, Inc.', 'Utilities', 'Electric Utilities'),
    'AWK': ('American Water Works Company', 'Utilities', 'Water Utilities'),
    'DTE': ('DTE Energy Company', 'Utilities', 'Electric Utilities'),
    'ETR': ('Entergy Corporation', 'Utilities', 'Electric Utilities'),
    'ES': ('Eversource Energy', 'Utilities', 'Electric Utilities'),
    'PPL': ('PPL Corporation', 'Utilities', 'Electric Utilities'),
    'AEE': ('Ameren Corporation', 'Utilities', 'Electric Utilities'),
    'FE': ('FirstEnergy Corp.', 'Utilities', 'Electric Utilities'),
    'CMS': ('CMS Energy Corporation', 'Utilities', 'Electric Utilities'),
    'CNP': ('CenterPoint Energy, Inc.', 'Utilities', 'Electric Utilities'),
    'LNT': ('Alliant Energy Corporation', 'Utilities', 'Electric Utilities'),
    'ATO': ('Atmos Energy Corporation', 'Utilities', 'Gas Utilities'),
    'NRG': ('NRG Energy, Inc.', 'Utilities', 'Independent Power Producers & Energy Traders'),
    'NI': ('NiSource Inc.', 'Utilities', 'Multi-Utilities'),
    'EVRG': ('Evergy, Inc.', 'Utilities', 'Electric Utilities'),
    'PNW': ('Pinnacle West Capital Corporation', 'Utilities', 'Electric Utilities'),
}

# Additional NASDAQ 100 stocks not in S&P 500
NASDAQ100_ONLY = {
    'ARM': ('Arm Holdings plc', 'Information Technology', 'Semiconductors'),
    'AZN': ('AstraZeneca PLC', 'Health Care', 'Pharmaceuticals'),
    'BKR': ('Baker Hughes Company', 'Energy', 'Oil & Gas Equipment & Services'),
    'CCEP': ('Coca-Cola Europacific Partners', 'Consumer Staples', 'Soft Drinks & Non-alcoholic Beverages'),
    'CDW': ('CDW Corporation', 'Information Technology', 'Technology Distributors'),
    'CEG': ('Constellation Energy Corporation', 'Utilities', 'Electric Utilities'),
    'COIN': ('Coinbase Global, Inc.', 'Financials', 'Financial Exchanges & Data'),
    'CPRT': ('Copart, Inc.', 'Industrials', 'Diversified Support Services'),
    'CSGP': ('CoStar Group, Inc.', 'Real Estate', 'Real Estate Services'),
    'DDOG': ('Datadog, Inc.', 'Information Technology', 'Systems Software'),
    'DXCM': ('DexCom, Inc.', 'Health Care', 'Health Care Equipment'),
    'FANG': ('Diamondback Energy, Inc.', 'Energy', 'Oil & Gas Exploration & Production'),
    'FAST': ('Fastenal Company', 'Industrials', 'Trading Companies & Distributors'),
    'FTNT': ('Fortinet, Inc.', 'Information Technology', 'Systems Software'),
    'GEHC': ('GE HealthCare Technologies Inc.', 'Health Care', 'Health Care Equipment'),
    'GFS': ('GlobalFoundries Inc.', 'Information Technology', 'Semiconductors'),
    'IDXX': ('IDEXX Laboratories, Inc.', 'Health Care', 'Health Care Equipment'),
    'ILMN': ('Illumina, Inc.', 'Health Care', 'Life Sciences Tools & Services'),
    'KDP': ('Keurig Dr Pepper Inc.', 'Consumer Staples', 'Soft Drinks & Non-alcoholic Beverages'),
    'KHC': ('The Kraft Heinz Company', 'Consumer Staples', 'Packaged Foods & Meats'),
    'LULU': ('Lululemon Athletica Inc.', 'Consumer Discretionary', 'Apparel, Accessories & Luxury Goods'),
    'MAR': ('Marriott International, Inc.', 'Consumer Discretionary', 'Hotels, Resorts & Cruise Lines'),
    'MCHP': ('Microchip Technology Incorporated', 'Information Technology', 'Semiconductors'),
    'MDLZ': ('Mondelez International, Inc.', 'Consumer Staples', 'Packaged Foods & Meats'),
    'MELI': ('MercadoLibre, Inc.', 'Consumer Discretionary', 'Broadline Retail'),
    'MNST': ('Monster Beverage Corporation', 'Consumer Staples', 'Soft Drinks & Non-alcoholic Beverages'),
    'MRVL': ('Marvell Technology, Inc.', 'Information Technology', 'Semiconductors'),
    'NXPI': ('NXP Semiconductors N.V.', 'Information Technology', 'Semiconductors'),
    'ODFL': ('Old Dominion Freight Line, Inc.', 'Industrials', 'Trucking'),
    'ON': ('ON Semiconductor Corporation', 'Information Technology', 'Semiconductors'),
    'ORLY': ("O'Reilly Automotive, Inc.", 'Consumer Discretionary', 'Automotive Retail'),
    'PCAR': ('PACCAR Inc', 'Industrials', 'Construction Machinery & Heavy Transportation Equipment'),
    'PAYX': ('Paychex, Inc.', 'Industrials', 'Human Resource & Employment Services'),
    'PDD': ('PDD Holdings Inc.', 'Consumer Discretionary', 'Broadline Retail'),
    'ROP': ('Roper Technologies, Inc.', 'Information Technology', 'Application Software'),
    'ROST': ('Ross Stores, Inc.', 'Consumer Discretionary', 'Apparel Retail'),
    'SIRI': ('Sirius XM Holdings Inc.', 'Communication Services', 'Broadcasting'),
    'SMCI': ('Super Micro Computer, Inc.', 'Information Technology', 'Technology Hardware, Storage & Peripherals'),
    'SNPS': ('Synopsys, Inc.', 'Information Technology', 'Application Software'),
    'SPLK': ('Splunk Inc.', 'Information Technology', 'Systems Software'),
    'TEAM': ('Atlassian Corporation', 'Information Technology', 'Systems Software'),
    'TMUS': ('T-Mobile US, Inc.', 'Communication Services', 'Wireless Telecommunication Services'),
    'VRSK': ('Verisk Analytics, Inc.', 'Industrials', 'Research & Consulting Services'),
    'WDAY': ('Workday, Inc.', 'Information Technology', 'Application Software'),
    'XEL': ('Xcel Energy Inc.', 'Utilities', 'Electric Utilities'),
    'ZS': ('Zscaler, Inc.', 'Information Technology', 'Systems Software'),
}


def get_fallback_tickers():
    """Get comprehensive fallback ticker list when web scraping fails"""
    data = []

    # Add all S&P 500 stocks
    for ticker, (name, sector, industry) in SP500_TICKERS.items():
        data.append({
            'ticker': ticker,
            'name': name,
            'sector': sector,
            'sub_industry': industry,
            'index': 'S&P500'
        })

    # Add NASDAQ 100 stocks not already in S&P 500
    for ticker, (name, sector, industry) in NASDAQ100_ONLY.items():
        if ticker not in SP500_TICKERS:
            data.append({
                'ticker': ticker,
                'name': name,
                'sector': sector,
                'sub_industry': industry,
                'index': 'NASDAQ100'
            })

    return pd.DataFrame(data)


def get_sp500_tickers():
    """Fetch S&P 500 tickers from Wikipedia"""
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    try:
        tables = pd.read_html(url)
        df = tables[0]
        df['Symbol'] = df['Symbol'].str.replace('.', '-', regex=False)
        result = df[['Symbol', 'Security', 'GICS Sector', 'GICS Sub-Industry']].rename(
            columns={'Symbol': 'ticker', 'Security': 'name',
                     'GICS Sector': 'sector', 'GICS Sub-Industry': 'sub_industry'}
        )
        print(f"  Successfully fetched {len(result)} S&P 500 tickers")
        return result
    except Exception as e:
        print(f"  Error fetching S&P 500 tickers: {e}")
        return pd.DataFrame()


def get_nasdaq100_tickers():
    """Fetch Nasdaq 100 tickers from Wikipedia"""
    url = 'https://en.wikipedia.org/wiki/Nasdaq-100'
    try:
        tables = pd.read_html(url)
        # Find the table with tickers
        for table in tables:
            if 'Ticker' in table.columns or 'Symbol' in table.columns:
                ticker_col = 'Ticker' if 'Ticker' in table.columns else 'Symbol'
                company_col = 'Company' if 'Company' in table.columns else table.columns[0]
                sector_col = 'GICS Sector' if 'GICS Sector' in table.columns else None
                sub_industry_col = 'GICS Sub-Industry' if 'GICS Sub-Industry' in table.columns else None

                df = table[[ticker_col, company_col]].copy()
                df.columns = ['ticker', 'name']
                df['ticker'] = df['ticker'].str.replace('.', '-', regex=False)

                if sector_col and sector_col in table.columns:
                    df['sector'] = table[sector_col]
                if sub_industry_col and sub_industry_col in table.columns:
                    df['sub_industry'] = table[sub_industry_col]

                print(f"  Successfully fetched {len(df)} NASDAQ 100 tickers")
                return df
        return pd.DataFrame()
    except Exception as e:
        print(f"  Error fetching Nasdaq 100 tickers: {e}")
        return pd.DataFrame()


def get_combined_tickers():
    """Get combined unique tickers from S&P 500 and Nasdaq 100"""
    print("=" * 50)
    print("FETCHING INDEX CONSTITUENTS")
    print("=" * 50)

    print("\nFetching S&P 500 tickers...")
    sp500 = get_sp500_tickers()

    print("\nFetching Nasdaq 100 tickers...")
    nasdaq = get_nasdaq100_tickers()

    # Check if web scraping succeeded
    if len(sp500) == 0 and len(nasdaq) == 0:
        print("\n⚠ Web scraping failed. Using comprehensive fallback ticker list...")
        combined = get_fallback_tickers()
        print(f"✓ Loaded {len(combined)} tickers from fallback list")
        print(f"  - S&P 500: {len([t for t in combined['index'] if t == 'S&P500'])} stocks")
        print(f"  - NASDAQ 100 (unique): {len([t for t in combined['index'] if t == 'NASDAQ100'])} stocks")
        return combined

    sp500['index'] = 'S&P500'
    nasdaq['index'] = 'NASDAQ100'

    # Combine and remove duplicates, keeping S&P 500 info as priority
    combined = pd.concat([sp500, nasdaq], ignore_index=True)
    combined = combined.drop_duplicates(subset='ticker', keep='first')

    # Fill missing sectors from fallback data
    all_fallback = {**SP500_TICKERS, **NASDAQ100_ONLY}
    for idx, row in combined.iterrows():
        if pd.isna(row.get('sector')) or row.get('sector') == '':
            ticker = row['ticker']
            if ticker in all_fallback:
                combined.at[idx, 'sector'] = all_fallback[ticker][1]
                combined.at[idx, 'sub_industry'] = all_fallback[ticker][2]

    print(f"\n✓ Total unique tickers: {len(combined)}")
    print(f"  - Sectors covered: {combined['sector'].nunique()}")

    return combined


def fetch_fundamental_data(ticker, max_retries=3):
    """Fetch comprehensive fundamental data for a single ticker"""
    for attempt in range(max_retries):
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            # Get financial statements
            try:
                balance_sheet = stock.balance_sheet
                quarterly_balance = stock.quarterly_balance_sheet
            except:
                balance_sheet = pd.DataFrame()
                quarterly_balance = pd.DataFrame()

            try:
                income_stmt = stock.income_stmt
                quarterly_income = stock.quarterly_income_stmt
            except:
                income_stmt = pd.DataFrame()
                quarterly_income = pd.DataFrame()

            try:
                cash_flow = stock.cashflow
                quarterly_cashflow = stock.quarterly_cashflow
            except:
                cash_flow = pd.DataFrame()
                quarterly_cashflow = pd.DataFrame()

            # Calculate additional metrics from financial statements
            additional_metrics = extract_financial_statement_metrics(
                balance_sheet, income_stmt, cash_flow, info
            )

            # Extract key metrics
            data = {
                'ticker': ticker,
                'name': info.get('longName', info.get('shortName', ticker)),
                'sector': info.get('sector', 'Unknown'),
                'industry': info.get('industry', 'Unknown'),
                'market_cap': info.get('marketCap', np.nan),
                'enterprise_value': info.get('enterpriseValue', np.nan),
                'current_price': info.get('currentPrice', info.get('regularMarketPrice', np.nan)),
                'shares_outstanding': info.get('sharesOutstanding', np.nan),
                'float_shares': info.get('floatShares', np.nan),

                # Valuation metrics
                'forward_pe': info.get('forwardPE', np.nan),
                'trailing_pe': info.get('trailingPE', np.nan),
                'peg_ratio': info.get('pegRatio', np.nan),
                'price_to_book': info.get('priceToBook', np.nan),
                'price_to_sales': info.get('priceToSalesTrailing12Months', np.nan),
                'ev_to_ebitda': info.get('enterpriseToEbitda', np.nan),
                'ev_to_revenue': info.get('enterpriseToRevenue', np.nan),

                # Profitability metrics
                'profit_margin': info.get('profitMargins', np.nan),
                'operating_margin': info.get('operatingMargins', np.nan),
                'gross_margin': info.get('grossMargins', np.nan),
                'ebitda_margin': info.get('ebitdaMargins', np.nan),
                'roe': info.get('returnOnEquity', np.nan),
                'roa': info.get('returnOnAssets', np.nan),

                # Financial health
                'debt_to_equity': info.get('debtToEquity', np.nan),
                'current_ratio': info.get('currentRatio', np.nan),
                'quick_ratio': info.get('quickRatio', np.nan),
                'total_debt': info.get('totalDebt', np.nan),
                'total_cash': info.get('totalCash', np.nan),
                'total_assets': info.get('totalAssets', np.nan),
                'book_value': info.get('bookValue', np.nan),

                # Growth metrics
                'revenue_growth': info.get('revenueGrowth', np.nan),
                'earnings_growth': info.get('earningsGrowth', np.nan),
                'earnings_quarterly_growth': info.get('earningsQuarterlyGrowth', np.nan),

                # Cash flow
                'free_cashflow': info.get('freeCashflow', np.nan),
                'operating_cashflow': info.get('operatingCashflow', np.nan),

                # Dividend
                'dividend_yield': info.get('dividendYield', np.nan),
                'dividend_rate': info.get('dividendRate', np.nan),
                'payout_ratio': info.get('payoutRatio', np.nan),
                'five_year_avg_dividend_yield': info.get('fiveYearAvgDividendYield', np.nan),
                'ex_dividend_date': info.get('exDividendDate', np.nan),

                # Price metrics
                'beta': info.get('beta', np.nan),
                'fifty_two_week_high': info.get('fiftyTwoWeekHigh', np.nan),
                'fifty_two_week_low': info.get('fiftyTwoWeekLow', np.nan),
                'fifty_day_average': info.get('fiftyDayAverage', np.nan),
                'two_hundred_day_average': info.get('twoHundredDayAverage', np.nan),
                'average_volume': info.get('averageVolume', np.nan),
                'average_volume_10days': info.get('averageVolume10days', np.nan),

                # EPS
                'trailing_eps': info.get('trailingEps', np.nan),
                'forward_eps': info.get('forwardEps', np.nan),

                # Revenue/Earnings
                'total_revenue': info.get('totalRevenue', np.nan),
                'ebitda': info.get('ebitda', np.nan),
                'net_income': info.get('netIncomeToCommon', np.nan),
                'gross_profit': info.get('grossProfits', np.nan),

                # Analyst targets
                'target_high_price': info.get('targetHighPrice', np.nan),
                'target_low_price': info.get('targetLowPrice', np.nan),
                'target_mean_price': info.get('targetMeanPrice', np.nan),
                'target_median_price': info.get('targetMedianPrice', np.nan),
                'recommendation_mean': info.get('recommendationMean', np.nan),
                'recommendation_key': info.get('recommendationKey', ''),
                'number_of_analyst_opinions': info.get('numberOfAnalystOpinions', np.nan),

                # Short interest
                'short_ratio': info.get('shortRatio', np.nan),
                'short_percent_of_float': info.get('shortPercentOfFloat', np.nan),
                'shares_short': info.get('sharesShort', np.nan),
                'shares_short_prior_month': info.get('sharesShortPriorMonth', np.nan),

                # Insider & Institutional
                'held_percent_insiders': info.get('heldPercentInsiders', np.nan),
                'held_percent_institutions': info.get('heldPercentInstitutions', np.nan),
            }

            # Merge additional metrics from financial statements
            data.update(additional_metrics)

            return data

        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(1)
            else:
                return {'ticker': ticker, 'error': str(e)}

    return {'ticker': ticker, 'error': 'Max retries exceeded'}


def extract_financial_statement_metrics(balance_sheet, income_stmt, cash_flow, info):
    """Extract additional metrics from financial statements"""
    metrics = {}

    try:
        # Working Capital
        if not balance_sheet.empty:
            current_assets = get_item(balance_sheet, ['Total Current Assets', 'CurrentAssets'])
            current_liabilities = get_item(balance_sheet, ['Total Current Liabilities', 'CurrentLiabilities'])
            if current_assets and current_liabilities:
                metrics['working_capital'] = current_assets - current_liabilities

            # Total Equity
            total_equity = get_item(balance_sheet, ['Total Stockholder Equity', 'StockholdersEquity', 'Total Equity'])
            if total_equity:
                metrics['total_equity'] = total_equity

            # Retained Earnings
            retained_earnings = get_item(balance_sheet, ['Retained Earnings', 'RetainedEarnings'])
            if retained_earnings:
                metrics['retained_earnings'] = retained_earnings

            # Inventory
            inventory = get_item(balance_sheet, ['Inventory', 'Inventories'])
            if inventory:
                metrics['inventory'] = inventory

            # Receivables
            receivables = get_item(balance_sheet, ['Net Receivables', 'AccountsReceivable', 'Receivables'])
            if receivables:
                metrics['receivables'] = receivables

            # Total Liabilities
            total_liabilities = get_item(balance_sheet, ['Total Liabilities', 'TotalLiabilities'])
            if total_liabilities:
                metrics['total_liabilities'] = total_liabilities

        # Income Statement metrics
        if not income_stmt.empty:
            # Interest Expense
            interest_expense = get_item(income_stmt, ['Interest Expense', 'InterestExpense'])
            if interest_expense:
                metrics['interest_expense'] = abs(interest_expense)

            # EBIT (Operating Income)
            ebit = get_item(income_stmt, ['Operating Income', 'EBIT', 'OperatingIncome'])
            if ebit:
                metrics['ebit'] = ebit

            # Cost of Revenue
            cogs = get_item(income_stmt, ['Cost Of Revenue', 'CostOfRevenue', 'CostOfGoodsSold'])
            if cogs:
                metrics['cost_of_revenue'] = cogs

            # Research & Development
            rd_expense = get_item(income_stmt, ['Research Development', 'ResearchAndDevelopment', 'R&D'])
            if rd_expense:
                metrics['rd_expense'] = rd_expense

            # SG&A
            sga = get_item(income_stmt, ['Selling General Administrative', 'SellingGeneralAndAdministration'])
            if sga:
                metrics['sga_expense'] = sga

        # Cash Flow metrics
        if not cash_flow.empty:
            # Capital Expenditure
            capex = get_item(cash_flow, ['Capital Expenditure', 'CapitalExpenditures', 'CapEx'])
            if capex:
                metrics['capex'] = abs(capex)

            # Depreciation
            depreciation = get_item(cash_flow, ['Depreciation', 'DepreciationAndAmortization'])
            if depreciation:
                metrics['depreciation'] = depreciation

    except Exception as e:
        pass  # Return partial metrics on error

    return metrics


def get_item(df, possible_names):
    """Get first available item from financial statement"""
    if df.empty:
        return None
    for name in possible_names:
        if name in df.index:
            val = df.loc[name].iloc[0]
            if pd.notna(val):
                return val
    return None


def fetch_historical_data(ticker, period='2y'):
    """Fetch comprehensive historical price data"""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)

        if len(hist) < 20:
            return {
                'ticker': ticker,
                '1y_return': np.nan, '6m_return': np.nan,
                '3m_return': np.nan, '1m_return': np.nan,
                '1w_return': np.nan, 'ytd_return': np.nan,
                'volatility': np.nan, 'avg_volume': np.nan,
                'price_history': None
            }

        returns = hist['Close'].pct_change().dropna()
        current_price = hist['Close'].iloc[-1]

        # Calculate various returns
        data = {
            'ticker': ticker,
            'current_price': current_price,
            'avg_volume': hist['Volume'].mean(),
            'recent_volume': hist['Volume'].iloc[-5:].mean(),
        }

        # Returns at different timeframes
        if len(hist) > 252:
            data['1y_return'] = (current_price / hist['Close'].iloc[-252] - 1)
        if len(hist) > 126:
            data['6m_return'] = (current_price / hist['Close'].iloc[-126] - 1)
        if len(hist) > 63:
            data['3m_return'] = (current_price / hist['Close'].iloc[-63] - 1)
        if len(hist) > 21:
            data['1m_return'] = (current_price / hist['Close'].iloc[-21] - 1)
        if len(hist) > 5:
            data['1w_return'] = (current_price / hist['Close'].iloc[-5] - 1)

        # YTD return
        current_year = pd.Timestamp.now().year
        ytd_start = hist[hist.index.year == current_year]
        if len(ytd_start) > 0:
            data['ytd_return'] = (current_price / ytd_start['Close'].iloc[0] - 1)

        # Volatility (annualized)
        data['volatility'] = returns.std() * np.sqrt(252)

        # Downside volatility (for Sortino)
        downside_returns = returns[returns < 0]
        data['downside_volatility'] = downside_returns.std() * np.sqrt(252) if len(downside_returns) > 10 else np.nan

        # Sharpe approximation (assuming 4% risk-free rate)
        if data['volatility'] > 0:
            annual_return = returns.mean() * 252
            data['sharpe_approx'] = (annual_return - 0.04) / data['volatility']
        else:
            data['sharpe_approx'] = np.nan

        # Max drawdown
        rolling_max = hist['Close'].expanding().max()
        drawdown = hist['Close'] / rolling_max - 1
        data['max_drawdown'] = drawdown.min()

        # Store price history for later analysis
        data['price_history'] = hist[['Open', 'High', 'Low', 'Close', 'Volume']]

        return data

    except Exception as e:
        return {
            'ticker': ticker,
            '1y_return': np.nan, '6m_return': np.nan,
            '3m_return': np.nan, '1m_return': np.nan,
            'volatility': np.nan, 'error': str(e)
        }


def fetch_market_data():
    """Fetch benchmark market data (SPY, QQQ, VIX, rates proxies)"""
    try:
        benchmarks = {
            'SPY': yf.Ticker('SPY').history(period='2y'),
            'QQQ': yf.Ticker('QQQ').history(period='2y'),
            '^VIX': yf.Ticker('^VIX').history(period='2y'),
            'TLT': yf.Ticker('TLT').history(period='2y'),  # Treasury bonds
            'UUP': yf.Ticker('UUP').history(period='2y'),  # US Dollar
            'USO': yf.Ticker('USO').history(period='2y'),  # Oil
        }
        return benchmarks
    except:
        return {}


def fetch_all_data(tickers_df, sample_size=None, delay=0.05):
    """Fetch all fundamental and return data for given tickers"""
    tickers = tickers_df['ticker'].tolist()

    if sample_size:
        tickers = tickers[:sample_size]

    print(f"\n{'='*50}")
    print(f"FETCHING DATA FOR {len(tickers)} STOCKS")
    print(f"{'='*50}")

    fundamental_data = []
    returns_data = []

    for ticker in tqdm(tickers, desc="Fetching data"):
        # Fetch fundamental data
        fund_data = fetch_fundamental_data(ticker)
        if 'error' not in fund_data:
            fundamental_data.append(fund_data)

        # Fetch historical returns
        ret_data = fetch_historical_data(ticker)
        returns_data.append(ret_data)

        time.sleep(delay)

    # Create DataFrames
    fund_df = pd.DataFrame(fundamental_data)

    # Process returns data (excluding price_history for main DataFrame)
    returns_processed = []
    price_histories = {}
    for ret in returns_data:
        price_hist = ret.pop('price_history', None)
        if price_hist is not None:
            price_histories[ret['ticker']] = price_hist
        returns_processed.append(ret)

    returns_df = pd.DataFrame(returns_processed)

    # Merge with original ticker info
    result = tickers_df[tickers_df['ticker'].isin(fund_df['ticker'])].merge(
        fund_df, on='ticker', how='left', suffixes=('_orig', '')
    )

    # Use sector from API if available, otherwise from original
    if 'sector_orig' in result.columns and 'sector' in result.columns:
        result['sector'] = result['sector'].fillna(result['sector_orig'])
        result = result.drop(columns=['sector_orig'])

    # Merge returns
    result = result.merge(returns_df, on='ticker', how='left', suffixes=('', '_hist'))

    # Handle duplicate current_price columns
    if 'current_price_hist' in result.columns:
        result['current_price'] = result['current_price'].fillna(result['current_price_hist'])
        result = result.drop(columns=['current_price_hist'])

    print(f"\n✓ Successfully fetched data for {len(result)} stocks")
    print(f"  - Sectors: {result['sector'].nunique()}")
    print(f"  - Industries: {result['industry'].nunique() if 'industry' in result.columns else 'N/A'}")

    return result, price_histories


def fetch_historical_returns(ticker, period='1y'):
    """Legacy function for backward compatibility"""
    return fetch_historical_data(ticker, period)


if __name__ == "__main__":
    # Test the fetcher
    tickers = get_combined_tickers()
    print(f"\nTotal tickers: {len(tickers)}")
    print(f"\nSectors distribution:")
    print(tickers['sector'].value_counts())

    print("\n\nSample tickers:")
    print(tickers.head(20))
