# Ekart Hub Performance Dashboard

## Deploy on Render.com (Free)

1. Push this folder to a GitHub repo
2. Go to render.com → New → Web Service
3. Connect your GitHub repo
4. Set these environment variables:
   - `OWNER_PASSWORD` = your secret password (change from default!)
   - `SECRET_KEY` = any random string
5. Click Deploy

## Usage

- **Everyone**: Open the Render URL to view dashboard (read-only)
- **Owner**: Click the ⚙️ button (bottom-right) → Enter password → Upload Excel file
- Dashboard auto-refreshes for viewers every 5 minutes

## Excel File Format Required
Columns: Date, Week, Month, GM, RM, AM, Hub Type, Hub Name, 
         Total Tickets, Response < 6 Hrs, Response < 24 hrs, 
         Closed By D0, Closed by D1
