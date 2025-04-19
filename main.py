import json
import os
from pathlib import Path
import pandas as pd
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from plotly_config import create_base_layout, apply_config_to_figure
from registry import WIDGETS, register_widget
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from openbb import obb
import datetime
import requests
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

origins = [
    "https://pro.openbb.co",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ROOT_PATH = Path(__file__).parent.resolve()


@app.get("/")
def read_root():
    return {"Info": "Full example for OpenBB Custom Backend"}


@app.get("/widgets.json")
async def get_widgets():
    return WIDGETS

@app.get("/oss-company-stats")
@register_widget({
    "name": "OSS Company Stats",
    "description": "Shows OSS companies stats",
    "category": "Equities",
    "type": "table",
    "endpoint": "oss-company-stats",
    "gridData": {"w": 40, "h": 15},
    "source": "FMP",
    "data": {
        "table": {
            "showAll": True,
            "columnsDefs": [
                {
                    "field": "Ticker",
                    "headerName": "Ticker",
                    "cellDataType": "text"
                },
                {
                    "field": "Name",
                    "headerName": "Name",
                    "cellDataType": "text"
                },
                {
                    "field": "Price Chg % (1W)",
                    "headerName": "1W Change",
                    "cellDataType": "number",
                    "renderFn": "greenRed"
                },
                {
                    "field": "Market Cap [B]",
                    "headerName": "Market Cap [B]",
                    "cellDataType": "text"
                },
                {
                    "field": "Total Revenues (LTM) [M]",
                    "headerName": "Revenue (LTM) [M]",
                    "cellDataType": "text"
                },
                {
                    "field": "1-Day %",
                    "headerName": "1D Change",
                    "cellDataType": "number",
                    "renderFn": "greenRed"
                },
                {
                    "field": "Total Return (1Y)",
                    "headerName": "1Y Return",
                    "cellDataType": "number",
                    "renderFn": "greenRed"
                },
                {
                    "field": "Total Return (3Y)",
                    "headerName": "3Y Return",
                    "cellDataType": "number",
                    "renderFn": "greenRed"
                },
                {
                    "field": "EV/Sales (LTM)",
                    "headerName": "EV/Sales",
                    "cellDataType": "text"
                }
            ]
        }
    }
})
def get_oss_company_stats():
    """Get OSS company stats."""
    try:
        # Define the list of tickers
        tickers = [
            'KLTR', 'COIN', 'BASE', 'CFLT', 'FROG', 'FSLY', 'MDB', 'ESTC',
            'PRGS', 'GTLB', 'HCP', 'RPD', 'DOCN',
        ]

        # Initialize empty lists to store data
        data = []

        # Get current date and dates for historical calculations
        end_date = datetime.datetime.now()
        start_date_3y = end_date - datetime.timedelta(days=3*365)
        start_date_1y = end_date - datetime.timedelta(days=365)
        start_date_1w = end_date - datetime.timedelta(days=7)

        for ticker in tickers:
            try:
                hist_3y = obb.equity.price.historical(
                    symbol=ticker,
                    start_date=start_date_3y.strftime('%Y-%m-%d'),
                    provider="fmp"
                ).to_df()
                hist_1y = hist_3y[hist_3y.index.map(lambda x: pd.Timestamp(x) > pd.Timestamp(start_date_1y))]
                hist_1w = hist_3y[hist_3y.index.map(lambda x: pd.Timestamp(x) > pd.Timestamp(start_date_1w))]
                hist = hist_1w[-2:]

                # Calculate returns
                def calculate_return(hist_data):
                    if len(hist_data) < 2:
                        return np.nan
                    try:
                        return ((hist_data['adj_close'].iloc[-1] / hist_data['adj_close'].iloc[0]) - 1) * 100
                    except (KeyError, IndexError):
                        return np.nan

                one_day_return = calculate_return(hist)
                one_week_return = calculate_return(hist_1w)
                one_year_return = calculate_return(hist_1y)
                three_year_return = calculate_return(hist_3y)

                company_name = obb.equity.fundamental.employee_count(ticker).to_df()["company_name"][0]
                market_cap = obb.equity.fundamental.metrics(ticker).to_df()["market_cap"][0]
                total_revenue = obb.equity.fundamental.income(ticker).to_df()["revenue"][0]
                ev_to_revenue = obb.equity.fundamental.metrics(ticker, provider="fmp").to_df()["ev_to_sales"][0]

                market_cap_in_b = float(market_cap) if market_cap else 0
                market_cap_in_b /= 1e9
                total_revenue_in_m = float(total_revenue) if total_revenue else 0
                total_revenue_in_m /= 1e6

                # Create row with all metrics
                row = {
                    'Ticker': ticker,
                    'Name': company_name,
                    'Price Chg % (1W)': one_week_return,
                    'Market Cap [B]': f"{market_cap_in_b:.2f}",
                    'Total Revenues (LTM) [M]': f"{total_revenue_in_m:.2f}",
                    '1-Day %': one_day_return,
                    'Total Return (1Y)': one_year_return,
                    'Total Return (3Y)': three_year_return,
                    'EV/Sales (LTM)': f"{ev_to_revenue:.1f}"
                }
                data.append(row)

            except Exception as e:
                print(f"Error processing {ticker}: {str(e)}")

        # Create DataFrame and sort
        df = pd.DataFrame(data)
        df = df.sort_values(by='Price Chg % (1W)', ascending=False)

        # Convert to dictionary for JSON response
        return df.to_dict(orient="records")

    except Exception as e:
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )

@app.get("/github-stats")
@register_widget({
    "name": "GitHub Repository Stats",
    "description": "Shows GitHub repository statistics",
    "category": "Open Source",
    "type": "table",
    "endpoint": "github-stats",
    "gridData": {"w": 40, "h": 15},
    "source": "GitHub",
    "data": {
        "table": {
            "showAll": True,
            "columnsDefs": [
                {
                    "field": "Repository",
                    "headerName": "Repository",
                    "cellDataType": "text"
                },
                {
                    "field": "Stars",
                    "headerName": "Stars",
                    "cellDataType": "number"
                },
                {
                    "field": "Forks",
                    "headerName": "Forks",
                    "cellDataType": "number"
                },
                {
                    "field": "Open Issues",
                    "headerName": "Open Issues",
                    "cellDataType": "number"
                },
                {
                    "field": "Last Update",
                    "headerName": "Last Update",
                    "cellDataType": "text"
                }
            ]
        }
    }
})
def get_github_stats():
    """Get GitHub repository statistics."""
    try:
        # Define the list of repositories to track
        repos = [
            'openbb-finance/OpenBB',
            'appsmithorg/appsmith',
            'hoppscotch/hoppscotch',
            'nocodb/nocodb',
            'calcom/cal.com',
            'remix-run/remix',
            'dagster-io/dagster',
            'cerbos/cerbos',
            'plane-org/plane',
            'bittensor/bittensor',
            'rustdesk/rustdesk',
            'traefik/traefik',
            'appflowy/appflowy',
            'researchhub/researchhub',
            'w4games/godot',
        ]

        # Initialize empty list to store data
        data = []

        for repo in repos:
            try:
                # Get repository stats
                stats = get_repo_stats(repo)
                if 'error' not in stats:
                    # Format the last update date
                    last_update = datetime.datetime.strptime(
                        stats['last_update'], 
                        '%Y-%m-%dT%H:%M:%SZ'
                    ).strftime('%Y-%m-%d %H:%M:%S')

                    # Create row with all metrics
                    row = {
                        'Repository': stats['repository'],
                        'Stars': stats['stars'],
                        'Forks': stats['forks'],
                        'Open Issues': stats['open_issues'],
                        'Last Update': last_update
                    }
                    data.append(row)

            except Exception as e:
                print(f"Error processing {owner}/{repo}: {str(e)}")

        # Create DataFrame and sort
        df = pd.DataFrame(data)
        df = df.sort_values(by='Stars', ascending=False)

        # Convert to dictionary for JSON response
        return df.to_dict(orient="records")

    except Exception as e:
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )

def get_repo_stats(repo: str) -> dict:
    """
    Get basic repository statistics
    """
    headers = {}

    token = os.getenv('GITHUB_TOKEN')
    if token:
        headers['Authorization'] = f'token {token}'
    
    try:
        url = f'https://api.github.com/repos/{repo}'
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise Exception(f'API request failed: {response.status_code}, {response.text}')
        
        data = response.json()
        return {
            'repository': f'{repo}',
            'stars': data['stargazers_count'],
            'forks': data['forks_count'],
            'open_issues': data['open_issues_count'],
            'last_update': data['updated_at']
        }
    
    except Exception as e:
        return {'error': str(e)}

