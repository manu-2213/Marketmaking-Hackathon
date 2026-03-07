from db import update_cash, upsert_position, log_trade


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
