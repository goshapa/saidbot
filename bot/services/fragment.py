def fragment_stars_link(username: str, quantity: int) -> str:
    """Deep link to Fragment's "buy stars" page with the recipient and
    quantity pre-filled, so the admin only has to open it and pay —
    no manual search. Fragment has no official API for this, this just
    saves the manual lookup step; the admin still completes the purchase
    themselves on fragment.com.
    """
    clean_username = username.strip().lstrip("@")
    return f"https://fragment.com/stars/buy?recipient={clean_username}&quantity={quantity}"
