from math import floor


def format_gbp(value, decimals=0, signed=False):
    amount = float(value or 0)
    magnitude = abs(amount)
    formatted = f"£{magnitude:,.{decimals}f}"
    if signed:
        sign = "+" if amount >= 0 else "-"
        return f"{sign}{formatted}"
    if amount < 0:
        return f"-{formatted}"
    return formatted


def dataframe_height(row_count, row_px=38, header_px=40, min_height=150, max_height=620):
    rows = max(1, int(row_count))
    return min(max_height, max(min_height, header_px + rows * row_px))


def team_cash_signature(teams):
    return tuple(sorted((name, round(details.get("cash", 0), 2)) for name, details in teams.items()))


def spread_signature(spreads):
    return tuple(
        sorted(
            (team, round(details.get("bid", 0), 4), round(details.get("ask", 0), 4))
            for team, details in spreads.items()
        )
    )
