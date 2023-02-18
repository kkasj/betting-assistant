import numpy as np
from typing import List, Optional

eps = 0.01

def float_equals(a, b):
    return abs(a-b) <= eps:

    
class ResultClassifier:
    bet_type_variables = [['1', 'x', '2'], # 1x2
                            ['over', 'under'], # under-over
                            ['1', '2'], # money-line
                            ['1', '2'], # asian-handicap
                            ['1x', '12', 'x2'], # double-chance
                            ['yes', 'no']] # both-teams-to-score
    
    bet_type_outcomes = [['1', 'x', '2'], # 1x2
                            ['over', 'under', 'half-over', 'half-under', '-'], # under-over
                            ['1', '2', '-'], # money-line
                            ['1', '2', 'half-1', 'half-2', '-'], # asian-handicap
                            ['1', 'x', '2'], # double-chance
                            ['yes', 'no']] # both-teams-to-score

    # in a strict bet the number of outcomes equals the number of variables
    @staticmethod
    def is_bet_strict(bet_type: int, bet_type_value: float | None) -> bool:
        n_impossible_outcomes = len(ResultClassifier.impossible_outcomes(bet_type, bet_type_value))
        if len(ResultClassifier.bet_type_outcomes[bet_type-1]) - n_impossible_outcomes == len(ResultClassifier.bet_type_variables[bet_type-1]):
            return True
        else:
            return False

    # a diagonal bet is a strict bet with a diagonal var2outcome odds matrix
    @staticmethod
    def is_bet_diagonal(bet_type: int, bet_type_value: float | None) -> bool:
        return ResultClassifier.is_bet_strict(bet_type, bet_type_value) and bet_type != 5


    @staticmethod
    def is_bet_asian(bet_type: int, bet_type_value: Optional[float]) -> bool: # an asian bet means under-over or asian-handicap bets with .25 or .75 bet type value
        if bet_type in (2, 4) and float_equals(bet_type_value % 0.5, 0.25):
            return True
        else:
            return False

    @staticmethod
    def impossible_outcomes(bet_type: int, bet_type_value: Optional[float]) -> List[int]:
        impossible = []

        if bet_type in (2, 4):
            # bet_type_value ends in .5 or .0 
            if not ResultClassifier.is_bet_asian(bet_type, bet_type_value):
                impossible += [2, 3]
            
            # ends in .5
            if float_equals(bet_type_value % 1, 0.5):
                impossible += [4]

        return impossible


    @staticmethod
    def classify(bet_type: int, bet_type_value: Optional[float], goals: List[int], partial_goals: List[int]) -> str:
        """
        Classifies the result with respect to the bet type.
        """
        
        if bet_type == 1 or bet_type == 5: # 1x2 and double-chance-> ['1', 'x', '2']
            r = goals[0] > goals[1]
            d = goals[0] == goals[1]

            return '1' if r else ('x' if d else '2')
        
        elif bet_type == 2: # under-over -> ['over', 'under', 'half-over', 'half-under', '-'] ('-' means return of stake)
            total_goals = sum(goals)

            diff = total_goals - bet_type_value

            if diff >= 0.5 - eps:
                return 'over'
            elif diff <= -0.5 + eps:
                return 'under'

            elif diff >= 0.25 - eps:
                return 'half-over'
            elif diff <= -0.25 + eps:
                return 'half-under'

            else:
                return '-' # stake returned
            
        elif bet_type == 3: # money-line -> ['1', '2', '-']
            r = goals[0] > goals[1]
            d = goals[0] == goals[1]

            return '1' if r else ('-' if d else '2') # if x, then return stake

        elif bet_type == 4: # asian-handicap -> ['1', '2', 'half-1', 'half-2', '-']
            diff = (goals[0] - goals[1]) + bet_type_value

            if diff >= 0.5 - eps:
                return '1'
            elif diff <= -0.5 + eps:
                return '2'

            elif diff >= 0.25 - eps:
                return 'half-1'
            elif diff <= -0.25 + eps:
                return 'half-2'

            else:
                return '-' # stake returned
        
        elif bet_type == 6: # both-teams-to-score (bts) -> ['yes', 'no']
            r = goals[0]>0 and goals[1]>0

            return 'yes' if r else 'no'
        
        else:
            raise ValueError


class Var2outcomeSchemaMethods: # defined in a separate class before Var2outcomeSchema in order to initalize static attributes in Var2outcomeSchema
    @staticmethod
    def _odds_coefficient(bet_type: int):
        outcomes = ResultClassifier.bet_type_outcomes[bet_type-1]
        variables = ResultClassifier.bet_type_variables[bet_type-1]

        # preallocation
        var2outcome_odds_coefficient = [[0 for i in range(len(outcomes))] for j in range(len(variables))]

        for j, variable in enumerate(variables):
            for i, outcome in enumerate(outcomes):
                # plain wins and double-chance handling
                if outcome == variable or outcome in list(variable): # e.g. '1' in '1x' or '2' == '2' or 'under' == 'under'
                    var2outcome_odds_coefficient[j][i] = 1 # to be multiplied by listed odds

                # half-wins
                elif outcome == 'half-' + variable:
                    var2outcome_odds_coefficient[j][i] = 0.5 # to be multiplied by listed odds

                # plain losses - do nothing

        return np.array(var2outcome_odds_coefficient)

    @staticmethod
    def _constant(bet_type: int):
        outcomes = ResultClassifier.bet_type_outcomes[bet_type-1]
        variables = ResultClassifier.bet_type_variables[bet_type-1]

        # preallocation
        var2outcome_constant = [[0 for i in range(len(outcomes))] for j in range(len(variables))]

        for j, variable in enumerate(variables):
            for i, outcome in enumerate(outcomes):
                # stake returned
                if outcome == '-':
                    var2outcome_constant[j][i] = 1

                # half-losses
                elif outcome[:5] == 'half-' and outcome != 'half-' + variable: # outcome starts with half but it's a half-loss
                    var2outcome_constant[j][i] = 0.5
                
                # plain losses - do nothing

        return np.array(var2outcome_constant)


class Var2outcomeSchema: # serves as a schema for creating var2outcome odds matrix for given listed odds and bet type
    bet_type_odds_coefficient = [Var2outcomeSchemaMethods._odds_coefficient(bet_type) for bet_type in range(1, 7)]
    bet_type_constant = [Var2outcomeSchemaMethods._constant(bet_type) for bet_type in range(1, 7)]


class Var2outcomeMatrix:
    @staticmethod
    def bet_type_var2outcome_odds(bet_type: int, listed_odds: List[float]) -> np.ndarray: # variable-to-outcome matrix with variable odds
        # error in parsing/storing odds
        if len(ResultClassifier.bet_type_variables[bet_type-1]) != len(listed_odds):
            return np.nan
        
        odds_coefficient = Var2outcomeSchema.bet_type_odds_coefficient[bet_type-1]

        listed_odds_diagonal = np.diag(listed_odds)

        var2outcome_odds = np.matmul(odds_coefficient.T, listed_odds_diagonal).T

        return var2outcome_odds

    @staticmethod
    def bet_type_var2outcome_constant(bet_type: int) -> np.ndarray: # variable-to-outcome matrix with constant odds (such as: return of stake, half-loss)
        var2outcome_constant = Var2outcomeSchema.bet_type_constant[bet_type-1]

        return var2outcome_constant

    @staticmethod
    def bet_type_var2outcome(bet_type: int, listed_odds: List[float]) -> np.ndarray:
        return Var2outcomeMatrix.bet_type_var2outcome_odds(bet_type, listed_odds) + Var2outcomeMatrix.bet_type_var2outcome_constant(bet_type)
        
