# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DealScout is a deal discovery and flip tracking app. It monitors Swoopa marketplace alerts (via Gmail), uses AI to classify items, looks up market prices on eBay, and notifies users of profitable deals.

## Architecture

```
Swoopa Emails → Gmail API → Gemini Classifier → eBay Lookup → SQLite DB → Push Notification
                                                                              ↓
                                                              React Native Mobile App
```

**Backend (FastAPI):** `backend/app/`
- `main.py` - App entry point, lifespan management, CORS, router registration
- `scheduler.py` - APScheduler jobs for email processing (5 min) and review reminders (15 min)
- `models.py` - SQLAlchemy models: Deal, Flip, Setting, DeviceToken
- `routers/` - API endpoints (deals, flips, stats)
- `services/` - Business logic (email_ingestion, gemini_classifier, ebay_lookup, notifications, profit_calculator)

**Mobile (React Native/Expo):** `mobile/`
- `App.tsx` - Navigation setup with bottom tabs
- `screens/` - DealsScreen, FlipsScreen, ProfitsScreen, SettingsScreen
- `services/` - API client, notification handling

## Common Commands

### Backend Development

```bash
cd backend

# Create/activate virtualenv
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run locally (port 8000)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Test eBay API lookup
python -c "
import asyncio
from app.services.ebay_lookup import get_market_value
result = asyncio.run(get_market_value('RTX 3080', 'used'))
print(result)
"

# Trigger email processing manually
python -c "
import asyncio
from app.scheduler import process_new_emails
asyncio.run(process_new_emails())
"
```

### Mobile Development

```bash
cd mobile

npm install
npx expo start          # Start Metro bundler
npx expo start --android  # Launch on Android
npx expo start --ios      # Launch on iOS
```

## Deployment

Backend runs on VPS at `dealscout.junipr.io` (port 8002 behind Caddy).

```bash
# Deploy updated code
rsync -avz --exclude '__pycache__' --exclude 'venv' --exclude '*.db' \
  backend/ junipr-vps:/home/deploy/dealscout/

# Restart service
ssh junipr-vps "sudo systemctl restart dealscout"

# Check logs
ssh junipr-vps "sudo journalctl -u dealscout -f"
```

## Key Data Flow

1. **Email Ingestion** (`services/email_ingestion.py`): Gmail API fetches Swoopa alerts, parses title/price/URL/source
2. **Classification** (`services/gemini_classifier.py`): Gemini Flash extracts category, brand, model, condition
3. **Price Lookup** (`services/ebay_lookup.py`): eBay Browse API gets current listing prices for market value estimate
4. **Profit Calculation** (`services/profit_calculator.py`): market_value - asking_price - fees
5. **Notification** (`services/notifications.py`): Firebase Cloud Messaging push to mobile app

## Environment Variables

Backend expects `.env` in `backend/` with:
- `GEMINI_API_KEY` - Google AI Studio
- `EBAY_APP_ID`, `EBAY_CERT_ID`, `EBAY_DEV_ID` - eBay Developer Program
- `GMAIL_CREDENTIALS_FILE`, `GMAIL_TOKEN_FILE` - Gmail OAuth
- `FIREBASE_CREDENTIALS_FILE`, `FIREBASE_PROJECT_ID` - Firebase Console
- `PROFIT_THRESHOLD`, `EBAY_FEE_PERCENTAGE` - App settings

## Database

SQLite by default (`dealscout.db`). Main tables:
- `deals` - Incoming deals with classification and pricing
- `flips` - Purchased inventory and completed sales
- `device_tokens` - FCM tokens for push notifications
- `settings` - Key-value app settings
