import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Any
from itertools import product as cartesian_product

from .result_classification import Var2outcomeMatrix 
from .bet_identifier import BetIdentifier
from . import utility


class Event:
    type = "Event"
    TAX: float = 0.88 # tax multiplier
    PART_KELLY: float = 0.4

    def __init__(self, probabilities: np.ndarray, var2outcome_odds: np.ndarray, bet_identifier: List[BetIdentifier], add_null_variable: bool = False, suppress_calculation: bool = True):
        self.bet_id: List[BetIdentifier] = bet_identifier[:]

        self.probabilities = probabilities
        self.n: int = self.probabilities.shape[0]
        self.m = var2outcome_odds.shape[0]

        # adding an additional null variable with odds 1 for every outcome (for the sake of combining events into a multievent)
        if add_null_variable:
            assert len(var2outcome_odds.shape) == 2
            self.var2outcome_odds = np.append(var2outcome_odds, np.ones(shape=(1, self.n)), axis=0)
            self.m += 1
        else:
            self.var2outcome_odds = var2outcome_odds
            
        self.varshape = [self.var2outcome_odds.shape[0]]

        if suppress_calculation:
            self.s = None
            self.keu = None
        else:
            self.calculate_bet_size()
    
    @classmethod
    def test_constructor(cls, probabilities: List[float], listed_odds: List[float], match_id: str, bet_type: int, bet_type_value: float | None = None):
        probabilities = np.array(probabilities)
        var2outcome_odds = Var2outcomeMatrix.bet_type_var2outcome(bet_type, listed_odds)

        return cls(probabilities, var2outcome_odds, [BetIdentifier(match_id, bet_type, bet_type_value)], add_null_variable=True)

    def get_events(self):
        return [self]

    def calculate_bet_size(self):
        uopt = utility.UtilityOptimizer(event=self) 
        self.s = self.PART_KELLY * uopt.kelly_bet_size()
        self.keu = uopt.expected_log_utility(self.s)
        self.calculated_prt = self.profit_ratio_tensor(self.s)

    def calculate_entangled_bet_size(self, ongoing_events):
        if len(ongoing_events) == 0:
            self.calculate_bet_size()
            return
        cuopt = utility.CollectiveUtilityOptimizer(ongoing_events=ongoing_events, event=self)
        self.s = self.PART_KELLY * cuopt.kelly_bet_size()
        self.keu = cuopt.expected_log_utility(self.s)
        self.calculated_prt = self.profit_ratio_tensor(self.s)
    

    def set_budget(self, retrieval_budget):
        self.retrieval_budget = retrieval_budget

    def profit_ratio_tensor(self, s: np.ndarray) -> np.ndarray:
        """
        Return a vector of possible profit-to-budget ratio values. 
        """

        return (self.TAX * self.var2outcome_odds.T - 1) @ s.reshape((-1, 1)).reshape((-1,))

    def profit_ratio(self, outcome: int) -> float:
        """
        Return profit-to-budget ratio of the outcome.
        """

        return (((self.TAX * self.var2outcome_odds.T - 1)[outcome]) @ self.s.reshape((-1, 1)))[0]

    def total_return(self, outcome: int) -> float:
        return self.retrieval_budget * (self.s.sum() + self.profit_ratio(outcome))

    def log_utility(self, outcome: int) -> float:
        """
        Calculate logarithmic utility of the outcome.
        """

        r = ((self.TAX*self.var2outcome_odds.T - 1)[outcome]) @ self.s 

        return np.log(r+1)[0]

    def __repr__(self) -> str:
        return ("Probabilities =\n"
                +f"{self.probabilities}\n"
                +f"Variable-to-outcome odds matrix =\n{self.var2outcome_odds}\n"
                +f"Optimal bet size =\n{self.s}\n"
                +f"Optimal expected log utility = {self.keu}\n"
                +f"Event type = {self.type}\n"
                +f"Bet Identifier = {self.bet_id}")



class MultiEvent(Event):
    type = "MultiEvent"
    def __init__(self, events: List[Event], rows = None):
        self.rows = rows
        self.events: List[Event] = [events[0]]
        super().__init__(np.copy(events[0].probabilities), np.copy(events[0].var2outcome_odds), events[0].bet_id)
        for event in events[1:]:
            self.add_event(event)

    @classmethod
    def from_event_list(cls, events: List[Event]):
        return cls(events)

    @classmethod
    def from_series(cls, events: np.ndarray):
        return cls(events.tolist(), rows=events)
    
    def get_events(self):
        """
        Return a list of subevents.
        """
        
        return self.events

    def add_event(self, event: Event):
        """
        Add an event to the multievent. 
        """

        assert event.type == "Event"
        assert len(event.var2outcome_odds.shape) == 2
    
        self.probabilities = np.multiply.outer(self.probabilities, event.probabilities)
        self.var2outcome_odds = np.moveaxis(np.multiply.outer(self.var2outcome_odds, event.var2outcome_odds), -2, 0)

        self.m *= event.m
        self.n *= event.n

        self.events.append(event)
        self.bet_id += event.bet_id
        self.varshape += event.varshape
    
        assert self.m * self.n == np.prod(self.var2outcome_odds.shape)
        assert len(self.var2outcome_odds.shape) == 2*len(self.events)

    def profit_ratio_tensor(self, s: np.ndarray) -> np.ndarray:
        """
        Return a tensor of possible profit-to-budget ratio values. 
        """

        assert len(s.shape) == len(self.events)
        return np.tensordot(self.TAX * self.var2outcome_odds - 1, s, axes=(np.arange(len(self.events)-1, -1, -1), np.arange(len(self.events))))

    def profit_ratio(self, outcomes: List[int]) -> float:
        """
        Return profit-to-budget ratio of the outcomes.
        """

        return self.calculated_prt[tuple(outcomes)]

    def total_return(self, outcomes: List[int]) -> float:
        """
        Total return of the outcomes = bet size + profit.
        """
        
        return self.retrieval_budget * (self.s.sum() + self.profit_ratio(outcomes))