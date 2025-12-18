from pathlib import Path

BASE_URL = "https://app.wallstreetsurvivor.com"
TRANSACTION_ENDPOINT = "/account/gettransactions"
HEADERS_ENDPOINT = "/account/transactionhistory"
REFERER_TRANSACTION_ENDPOINT = "/account/transactionhistory"
REFERER_HEADERS_ENDPOINT = "/account/dashboardv2"

DATA_DIR = Path("data")
DATA_DIR.mkdir(parents=True, exist_ok=True)
PARQUET_FILENAME = DATA_DIR / "transactions.parquet"
