import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / '.env')
DATA = ROOT / 'data'
GENERATED = ROOT / 'generated'
DB_PATH = DATA / 'copilot.sqlite3'

def provider() -> str:
    return os.getenv('MODEL_PROVIDER', 'demo')

SCHEMA = {
    'products': {'sku_id':'TEXT','product_name':'TEXT','category':'TEXT','unit_cost_usd':'REAL','selling_price_usd':'REAL'},
    'campaign_daily_metrics': {
        'id':'INT','report_date':'TEXT','sku_id':'TEXT','platform':'TEXT','creator_handle':'TEXT','hook_style':'TEXT',
        'impressions':'INT','views_3s':'INT','clicks':'INT','orders':'INT','ad_spend_usd':'REAL','gmv_usd':'REAL'
    }
}
