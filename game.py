from db import update_cash, upsert_position, log_trade, get_teams, get_positions, get_true_prices, get_round_history
import numpy as np


def find_market_maker(spreads):
    if not spreads:
        return None
    return min(spreads, key=lambda t: (spreads[t]["ask"] - spreads[t]["bid"], t))


def execute_trade(buyer, seller, stk, price, qty, rnd):
    cost = price * qty
    update_cash(buyer, -cost)
    update_cash(seller, +cost)
    upsert_position(buyer, stk, +qty, +cost)
    upsert_position(seller, stk, -qty, -cost)
    log_trade(rnd, stk, buyer, seller, price, qty)


def compute_team_sortino_ratios():
    """Compute Sortino ratios for all teams based on portfolio performance across rounds.
    
    Sortino ratio = (return - risk_free_rate) / downside_deviation
    Only penalizes downside volatility (negative returns), not upside.
    """
    teams = get_teams()
    positions = get_positions()
    true_prices = get_true_prices()
    round_history = get_round_history()
    
    # Current prices
    current_prices = true_prices.copy() if true_prices else {}
    
    sortino_ratios = {}
    
    for team_name, team_data in teams.items():
        # Calculate current portfolio value
        portfolio_value = team_data.get("cash", 0)
        
        # Add position values at current prices
        for pos in positions:
            if pos["team"] == team_name and pos["qty"] != 0:
                stock = pos["stock"]
                price = current_prices.get(stock, 0)
                portfolio_value += pos["qty"] * price
        
        # Calculate return on initial investment
        initial_cash = 100000
        total_return = portfolio_value - initial_cash
        return_pct = (total_return / initial_cash) * 100 if initial_cash > 0 else 0
        
        # Estimate downside deviation from position concentration and losses
        # A perfect market maker would have minimal position variance
        downside_dev = 0
        position_values = []
        has_losses = False
        
        for pos in positions:
            if pos["team"] == team_name and pos["qty"] != 0:
                stock = pos["stock"]
                price = current_prices.get(stock, 0)
                position_value = pos["qty"] * price
                cost_basis = pos["cost_basis"]
                position_values.append(position_value)
                
                # Loss from this position
                loss = cost_basis - position_value
                if loss > 0:
                    downside_dev += loss ** 2
                    has_losses = True
        
        # Downside volatility calculation
        if downside_dev > 0:
            downside_dev = (downside_dev ** 0.5) / initial_cash * 100
        else:
            downside_dev = 0.1  # Minimal downside if no losses
        
        # Sortino ratio: return / downside_deviation
        # Risk-free rate approximation: 0 (or use 2% if desired)
        if downside_dev > 0.01:
            sortino = return_pct / downside_dev
        else:
            # No downside risk, Sortino is essentially the return itself
            sortino = return_pct * 10 if return_pct > 0 else 0
        
        sortino_ratios[team_name] = round(sortino, 2)
    
    return sortino_ratios
