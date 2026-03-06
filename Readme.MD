# 📈 Stock Prediction Market — Hackathon Game

A live bid-ask spread market-making game for ML hackathons.

## How it works

1. Each round covers one stock (stock_1 → stock_9)
2. Every team submits a **bid** and **ask** price
3. The team with the **tightest spread** becomes the **market maker**
4. Other teams choose to BUY (at ask) or SELL (at bid) from the market maker
5. Admin reveals the true price — leaderboard updates live
6. After 9 rounds, highest portfolio value wins

**Market maker rules:**
- Cannot refuse any trade
- Can go negative (borrow freely)
- Earns the spread on every trade executed through them

## Deployment (Streamlit Community Cloud — free)

1. Push this repo to GitHub (public or private)
2. Go to https://share.streamlit.io
3. Connect your GitHub account
4. Select `app.py` as the main file
5. Click Deploy — you get a shareable URL instantly

## Running locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Admin setup

- Open the sidebar, enter the admin password (default: `admin123`)
- **Change the password** in `app.py` line: `ADMIN_PASSWORD = "admin123"`
- Register all teams before the game starts

## Round flow (admin controls)

| Step | Admin action |
|------|-------------|
| Teams submit spreads | Wait, watch submissions appear live |
| Close submissions | Click "Close submissions → Trading" |
| Teams trade | Execute each buy/sell decision |
| Reveal price | Enter true price, click "Reveal & settle" |
| Next round | Click "Next round" |

## Scoring

Teams are ranked by **total portfolio value** = cash + unrealised P&L on open positions.
The leaderboard updates live after every trade.

## Files

- `app.py` — the full Streamlit app
- `requirements.txt` — Python dependencies
- `synthetic_regression_generator.py` — dataset generator (run separately on day 1)