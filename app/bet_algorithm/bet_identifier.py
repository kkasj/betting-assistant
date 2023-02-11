import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import Tuple

@dataclass(unsafe_hash=True)
class BetIdentifier:
    match_id: str
    bet_type: int
    bet_type_value: float | None

    def __init__(self, match_id: str, bet_type: int, bet_type_value: float):
        self.match_id = match_id
        self.bet_type = bet_type
        if pd.isnull(bet_type_value):
            self.bet_type_value = None
        else:
            self.bet_type_value = bet_type_value

@dataclass
class MultiBetIdentifier:
    bet_identifiers: Tuple[BetIdentifier]