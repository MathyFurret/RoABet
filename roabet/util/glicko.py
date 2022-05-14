"""
Glicko-1 rating implementation
"""
from __future__ import annotations

import math
from typing import NamedTuple

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterable

# pre-computed derived constants
Q = math.log(10) / 400
Q_SQUARED = Q**2
PI_SQUARED = math.pi**2

# system constants
DEFAULT_RATING = 1500
DEFAULT_DEVIATION = 350
MIN_DEVIATION = 50

# t* = number of absent rating cycles to return from MIN_DEVIATION to DEFAULT_DEVIATION
T_STAR = 30
C_SQUARED = (DEFAULT_DEVIATION**2 - MIN_DEVIATION**2)/T_STAR

class Rating(NamedTuple):
    rating: int
    dev: int

def tick_rating(old: Rating) -> Rating:
    """
    Performs Step 1 of calculation: initial increase of RD at the end of a rating cycle
    """
    return Rating(old.rating, min(round((old.dev**2 + C_SQUARED)**0.5), 350))

def _g(dev: float) -> float:
    return (1 + 3*Q_SQUARED * dev**2 / PI_SQUARED)**-0.5

def _e(r, r_opp, dev_opp):
    """
    expected score given ratings and opponent rating deviation
    """
    return 1/(1 + 10**(-_g(dev_opp)*(r-r_opp)/400))

def update_rating(old: Rating, matches: Iterable[tuple[Rating, float]]) -> Rating:
    """
    Performs Step 2 of calculation: update rating and RD based on results of games this cycle
    """
    if len(matches) == 0:
        return old
    
    inv_d_squared = Q_SQUARED * sum(
        _g(opp.dev)**2 
        * _e(old.rating, opp.rating, opp.dev)
        * (1 - _e(old.rating, opp.rating, opp.dev))
        for opp, score in matches)
    
    delta_r = sum(
        _g(opp.dev)
        * (score - _e(old.rating, opp.rating, opp.dev))
        for opp, score in matches
    ) * Q / (old.dev**-2 + inv_d_squared)

    r = round(old.rating + delta_r)
    dev = max(round((old.dev**-2 + inv_d_squared)**-0.5), MIN_DEVIATION)

    return Rating(r, dev)
