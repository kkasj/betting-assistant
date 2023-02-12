import pandas as pd
import numpy as np
from scipy.optimize import minimize
from typing import List, Dict
from itertools import product as cartesian_product
from time import time


class UtilityOptimizer:
    def __init__(self, event):
        self.event = event

    def expected_log_utility(self, s: np.ndarray) -> float:
        """
        Calculate expected logarithmic utility given the bet size.
        """

        s = s.reshape(self.event.varshape)
        prt: np.ndarray = self.event.profit_ratio_tensor(s)
        if np.any(prt <= -1):
            return -100
        else:
            return np.sum(self.event.probabilities * np.log(1 + prt))

    def kelly_bet_size(self) -> np.ndarray:
        """
        Return a bet size vector that optimizes logarithmic utility.
        """

        result = minimize(lambda x: -self.expected_log_utility(x), 
                        (1/(self.event.m+1))*np.random.random(self.event.m), 
                        constraints=[{'type': 'ineq', 'fun': lambda x: 1-x.sum()},
                                    {'type': 'eq', 'fun': lambda x: x[-1]}], 
                        bounds=[(0,1)]*self.event.m, 
                        tol=0.0001)
        s = result.x.reshape((-1,))
        s *= s>0.01 # discard small bet sizes

        if self.expected_log_utility(s) <= 1e-6:
            return np.array([0 for _ in range(self.event.m)]).reshape(self.event.varshape)
        
        return s.reshape(self.event.varshape)

class CollectiveUtilityOptimizer:
    def __init__(self, ongoing_events, event):
        self.ongoing_events = ongoing_events
        self.event = event

        self.unique_bet_ids = {bet_id for e in ongoing_events+[event] for bet_id in e.bet_id}
        self.basis = {bet_id: count for count, bet_id in enumerate(self.unique_bet_ids)} # maps to the index of the outcome in the cartesian product tuple
        self.basis_n = {bet_id: e.n for me in ongoing_events+[event] for bet_id, e in zip(me.bet_id, me.get_events())}
        self.broadcast_shape = tuple(map(lambda x: self.basis_n[x], self.basis))
        self.basis_probabilities = {bet_id: e.probabilities for me in ongoing_events+[event] for bet_id, e in zip(me.bet_id, me.get_events())}
        self.probabilities_list = list(map(lambda x: self.basis_probabilities[x], self.basis))

        # total budget - sizes of ongoing bets included
        self.total_budget = self.event.retrieval_budget + np.sum([e.retrieval_budget * e.s.sum() for e in self.ongoing_events])
        self.current_bet_size = np.sum([e.retrieval_budget/self.total_budget * np.sum(e.s) for e in self.ongoing_events])
        self.probabilities = self.create_probability_tensor()

        self.ongoing_diff_to_basis = [self.unique_bet_ids - set(e.bet_id) for e in ongoing_events]
        self.event_diff_to_basis = self.unique_bet_ids - set(self.event.bet_id)
        perm = {self.basis[bid]: ind for ind, bid in enumerate(self.event.bet_id + list(self.event_diff_to_basis))}
        self.event_transpose_order = tuple(perm[k] for k in range(len(self.basis)))
        self.event_expand_dims = tuple(range(-1, -1-len(self.event_diff_to_basis), -1))

        self.ongoing_prt = np.sum([self.broadcast_ongoing_prt(e.calculated_prt, ind) for ind, e in enumerate(ongoing_events)], axis=0)
        self.expected_ongoing_log_utility = np.sum(self.probabilities * np.log(1+self.ongoing_prt))
    
    def create_probability_tensor(self):
        """
        Create a probability tensor with axes matching the bet id basis.
        """

        prob = self.probabilities_list[0]
        for p in self.probabilities_list[1:]:
            prob = np.multiply.outer(prob, p)
        return prob

    def broadcast_ongoing_prt(self, prt: np.ndarray, event_ind: int) -> np.ndarray:
        """
        Broadcast and tranpose the profit-to-ratio tensor of ongoing events to bet id basis.
        """
        
        if len(self.ongoing_diff_to_basis[event_ind]) > 0:
            prt = np.expand_dims(prt, tuple(range(-1, -1-len(self.ongoing_diff_to_basis[event_ind]), -1)))
        perm = {self.basis[bid]: ind for ind, bid in enumerate(self.ongoing_events[event_ind].bet_id + list(self.ongoing_diff_to_basis[event_ind]))}
        prt = prt.transpose([perm[k] for k in range(len(self.basis))])
        prt = np.broadcast_to(prt, self.broadcast_shape)
        return prt

    def broadcast_event_prt(self, prt: np.ndarray) -> np.ndarray:
        """
        Broadcast and tranpose the event profit-to-ratio tensor to bet id basis.
        """

        if len(self.event_expand_dims) > 0:
            prt = np.expand_dims(prt, self.event_expand_dims)
        prt = prt.transpose(self.event_transpose_order)
        prt = np.broadcast_to(prt, self.broadcast_shape)
        return prt
    
    def expected_log_utility(self, s: np.ndarray):
        s = s.reshape(self.event.varshape)
        prt: np.ndarray = self.event.profit_ratio_tensor(s)
        prt = self.broadcast_event_prt(prt)
        total_prt = prt + self.ongoing_prt
        if np.any(total_prt <= -1):
            return -100
        else:
            return np.sum(self.probabilities * np.log(1 + total_prt))

    def kelly_bet_size(self) -> np.ndarray:
        """
        Return a bet size vector that optimizes logarithmic utility.
        """

        result = minimize(lambda x: -self.expected_log_utility(x), 
                        (1/(1+self.event.m))*np.random.random(self.event.m), 
                        constraints=[{'type': 'ineq', 'fun': lambda x: 1-self.current_bet_size-x.sum()},
                                    {'type': 'eq', 'fun': lambda x: x[-1]}], 
                        bounds=[(0,1)]*self.event.m, 
                        tol=0.0001)
        s = result.x
        s *= s>0.01 # discard small bet sizes

        if self.expected_log_utility(s) <= self.expected_ongoing_log_utility + 1e-6:
            return np.array([0 for _ in range(self.event.m)]).reshape(self.event.varshape)

        s *= self.total_budget/self.event.retrieval_budget 

        return s.reshape(self.event.varshape)
