def fragment_stars_link(quantity: int) -> str:
    """Link to Fragment's "buy stars" page with the quantity pre-filled.

    Fragment's `recipient` query param is not the plain @username — it's an
    opaque token Fragment itself generates once you search for that user on
    their site, and there's no public way to produce it ourselves. So the
    admin still has to search the recipient by hand on Fragment; only the
    quantity is pre-filled here to save that one step.
    """
    return f"https://fragment.com/stars/buy?quantity={quantity}"
