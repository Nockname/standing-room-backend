# Standing Room Backend

Scrapes TKTS and TDF websites for Broadway discount tickets and stores them in Supabase.

## What it does

- Gets TKTS booth data for available discounts every 3 minutes
- Checks TDF member offers
- Updates Supabase database
- Sends email notifications when new deals appear

## Setup

1. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Add your credentials to `keys/keys.py`:
```python
SUPABASE_URL = "your-url"
SUPABASE_KEY = "your-key"
EMAIL = "your-email"
EMAIL_PASSWORD = "your-password"
```

3. Run locally:
```bash
python -m tdf.main        # TDF 
cd tkts && python updateDatabase.py  # TKTS 
```

## GitHub Actions

Two workflows run automatically every 3 minutes:
- `update-database.yml` - Updates TKTS data
- `send-emails.yml` - Sends notifications

You need to add these secrets in repo settings:
- `SUPABASE_URL`
- `SUPABASE_KEY`
- `EMAIL`
- `EMAIL_PASSWORD`

## Structure

- `tkts/` - TKTS scraper and database code
- `tdf/` - TDF scraper and email sender
