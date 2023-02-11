"""
Module for probability inference.

The leading idea behind inference is extracting bookmaker's margin from listed odds, 
which leaves the possibility of easily calculating the probabilities as the inverse of fair odds.
"""

import numpy as np
import numpy.linalg as la
import scipy.optimize as opt 
from typing import List, Optional, Dict

from .result_classification import Var2outcomeMatrix, ResultClassifier
    

def infer_impossible_outcomes(bet_type: int, bet_type_value: Optional[float] = None) -> List[int]:
    """
    Infer impossible outcomes based on bet type.
    """
    
    zero_prob_outcomes = ResultClassifier.impossible_outcomes(bet_type, bet_type_value)

    return zero_prob_outcomes


def infer(odds: List[float], bet_type: int, bet_type_value: Optional[float] = None):
    """
    Infer probabilities of outcomes based on bet type and listed odds.

    The most reliable odds for inference are Pinnacle odds, but odds of any bookmaker can give a rough estimate.
    """

    m = len(odds)
    n = len(ResultClassifier.bet_type_outcomes[bet_type-1])

    var2outcome_odds = Var2outcomeMatrix.bet_type_var2outcome_odds(bet_type, odds)
    var2outcome_constant = Var2outcomeMatrix.bet_type_var2outcome_constant(bet_type)

    # preliminary inference
    zero_prob = infer_impossible_outcomes(bet_type, bet_type_value)

    # eliminate the preliminarily inferred probabilities
    var2outcome_odds = var2outcome_odds[:, [e for e in range(n) if e not in zero_prob]]
    var2outcome_constant = var2outcome_constant[:, [e for e in range(n) if e not in zero_prob]]
    n -= len(zero_prob)


    def fair_odds(matrix: np.ndarray, margin: float):
        result = np.vectorize(lambda x: 0 if x==0 else 1/(1/x - margin/m)) (matrix)
        result -= 1
        return result


    if m == n:
        # no constant probability coefficients -> we can extract margin and odds from lhs by multiplying by 1/odds - M/m
        if np.min(var2outcome_constant) == 0 and np.max(var2outcome_constant) == 0:
            variable_odds = np.max(var2outcome_odds, axis=1, keepdims=True)
            rhs = np.append(1/variable_odds, [[1]], axis=0)

            lhs = np.append(var2outcome_odds/variable_odds, np.ones(shape=(1, n)), axis=0)
            lhs = np.append(lhs, np.append(1/m * np.ones(shape=(m, 1)), [[0]], axis=0), axis=1)

            solution = la.solve(lhs, rhs).reshape((-1,))[:n]

        else:
            def f(pM: np.ndarray): # pm is a vector consisting of probabilities (p) and margin (m)
                # make sure pm is a vertical vector
                pM = pM.reshape((-1, 1))

                p = pM[:-1, :] # probabilities
                M = pM[-1, 0] # margin

                const_term = np.append(np.zeros(shape=(m,1)), [[-1]], axis=0)

                A = fair_odds(var2outcome_odds, M) + var2outcome_constant
                A = np.append(A, np.ones(shape=(1, n)), axis=0)

                return (np.matmul(A, p) + const_term).reshape((-1,))

            x0 = np.append((1/n) * np.ones(shape=(n,)), [0.05])
            solution = opt.fsolve(func=f, x0=x0).reshape((-1,))[:n]


    # elif m == n-1:
    #     # assume margin value
    #     M = 0.049896

    #     rhs = np.append(np.zeros(shape=(m,1)), [[1]], axis=0)

    #     lhs = fair_odds(var2outcome_odds, M) + var2outcome_constant
    #     lhs = np.append(lhs, np.ones(shape=(1, n)), axis=0)

    #     solution = la.solve(lhs, rhs).reshape((-1, 1))

    else: # m < n-1
        return np.nan


    # insert back the preliminarily inferred probabilities
    if len(zero_prob) != 0:
        solution = np.insert(solution, [elem-count for count, elem in enumerate(zero_prob)], [0 for _ in zero_prob])

    return solution.reshape((-1,))
