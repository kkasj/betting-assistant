import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from . import probability
from . import utils
from .result_classification import ResultClassifier, Var2outcomeMatrix
from .events import Event
from .bet_identifier import BetIdentifier
from ..scraper.aliases import bks, polish_bks, foreign_bks


def change_dates_format(data: pd.DataFrame) -> pd.DataFrame:
    """
    Adjust date format in the DataFrame to "<year>,<month>,<day>,<hour>,<minute>" with no padded zeros.
    """

    def remove_padded_zeros(number: str) -> str:
        return str(int(number))


    # 'Retrieval date' -> remove padded zeros and reorder to match column 'Date'
    new_order = [2, 1, 0, 3, 4]
    data["Retrieval date"] = data["Retrieval date"].apply(lambda date: ','.join([remove_padded_zeros(date.split(',')[i]) for i in new_order]))

    # 'Date' -> remove padded zeros
    data["Date"] = data["Date"].apply(lambda date: ','.join(map(remove_padded_zeros, date.split(','))))

    return data

def add_approximate_end_date(data: pd.DataFrame) -> pd.DataFrame:
    """
    Add a 'End date' column and deletes 'Date' column from the DataFrame.

    'End date' is an approximate time when the given event will end. 
    It is approximated to be two hours after the start date.
    """

    end_dates = data["Date"].apply(lambda date: utils.datetime2str(utils.str2datetime(date)+timedelta(hours=2)))
    data["End date"] = end_dates
    data = data.drop("Date", axis=1)

    # reorder columns
    data = data[[data.columns.tolist()[-1]] + data.columns.tolist()[:-1]]

    # drop rows with retrieval date later than end date
    data = data[data.apply(lambda x: utils.later_date_str(x["Retrieval date"], x["End date"]), axis=1)]

    return data

def filter_rows(data: pd.DataFrame) -> pd.DataFrame:
    """
    Filter entries in the DataFrame.
    """

    # keep only diagonal bets
    data = data[data.apply(lambda x: ResultClassifier.is_bet_diagonal(x["Bet type"], x["Bet type value"]), axis=1)]

    # filter bet types
    # selected_bet_types = [1]
    # data = data[data.apply(lambda x: x["Bet type"] in selected_bet_types, axis=1)]

    # drop asian bets
    # data = data[data.apply(lambda x: not ResultClassifier.is_bet_asian(x["Bet type"], x["Bet type value"]), axis=1)]

    # filter out rows with no results
    data = data[data.apply(lambda x: not np.any(pd.isna(x["Result"])), axis=1)]

    # filter out rows where the number of listed odds doesn't match the correct value for the given bet type
    data = data[data.apply(lambda x: len(x["25"]) == len(ResultClassifier.bet_type_variables[x["Bet type"]-1]), axis=1)]


    # TODO: add new filters

    data = data.reset_index(drop=True)

    return data

def index_by(data: pd.DataFrame, levels=["Retrieval date", "ID", "Bet type", "Bet type value"]) -> pd.DataFrame:
    """
    Create a MultiIndex DataFrame.
    """

    data = data.set_index(levels, drop=True)    

    return data

def sort_by_index(data: pd.DataFrame, level: str) -> pd.DataFrame:
    """
    Sort by a specified index level.
    """

    if level in ("Date", "Retrieval date", "End date", "Date spec"): # sort date in "Y,M,D,H,M" format
        sort_key = lambda dates: dates.map(lambda date: (int(elem) for elem in date.split(',')))
        return data.sort_index(axis=0, level=level, key=sort_key)
    else:
        return data.sort_index(axis=0, level=level)

def sort_by_column(data: pd.DataFrame, column: str) -> pd.DataFrame:
    """
    Sort by a specified column.
    """

    if column in ("Date", "Retrieval date", "End date", "Date spec"): # sort date in "Y,M,D,H,M" format
        sort_key = lambda dates_col: dates_col.apply(lambda date: tuple(int(elem) for elem in date.split(',')))
        return data.sort_values(axis=0, by=column, key=sort_key)
    else:
        return data.sort_values(axis=0, by=column)

def separate_bookmakers(data: pd.DataFrame) -> pd.DataFrame:
    """
    Melt the dataframe with respect to the bookmakers columns.

    Adds a new index level 'Bookmaker'. Requires 'data' to be a MultiIndex DataFrame. 
    """

    bk_cols = [str(bk) for bk in bks]
    non_bk_cols = [col for col in data.columns.tolist() if col not in bk_cols]

    data = pd.melt(data, id_vars=non_bk_cols, value_vars=bk_cols, var_name="Bookmaker", value_name="Odds", ignore_index=True)
    data = data.dropna(subset=["Odds"])
    
    return data
    
def filter_invalid_odds(data: pd.DataFrame) -> pd.DataFrame:
    bet_values_series = data.apply(lambda x: [prob*odds for prob, odds in zip(x["Probability"], x["Odds"])], axis=1)
    f = bet_values_series.apply(lambda x: not np.any([elem > 1.25 for elem in x])) # likely bad data

    data = data[f]
    return data

def add_var2outcome_column(data: pd.DataFrame) -> pd.DataFrame:
    """
    Create variable-to-outcome odds matrix for each row.
    """
    
    data['var2outcome'] = data.apply(lambda x: Var2outcomeMatrix.bet_type_var2outcome(x["Bet type"], x["Odds"]), axis=1)

    data = data.dropna(subset=['var2outcome'])

    return data

def add_probability_column(data: pd.DataFrame) -> pd.DataFrame:
    """
    Infer probability for each row.
    """
    
    data["Probability"] = data.apply(lambda x: probability.infer(x["25"], x["Bet type"], x["Bet type value"]), axis=1)

    return data

def add_outcome_column(data: pd.DataFrame) -> pd.DataFrame:
    """
    Classify result for each row.
    """
    
    data['Outcome'] = data.apply(lambda x: ResultClassifier.bet_type_outcomes[x["Bet type"]-1].index(ResultClassifier.classify(x["Bet type"], x["Bet type value"], x["Result"], x["Partial results"])), axis=1)

    data = data.drop(["Result", "Partial results"], axis=1)

    return data

def add_bet_id_column(data: pd.DataFrame) -> pd.DataFrame:
    data['Bet ID'] = data.apply(lambda x: BetIdentifier(x["ID"], x["Bet type"], x["Bet type value"]), axis=1)
    return data

def add_retrieval_batch_column(data: pd.DataFrame) -> pd.DataFrame:
    data["Retrieval batch"] = data.apply(lambda x: x["Retrieval date"] if len(x["Retrieval date"].split(',')[-1]) == 1 else x["Retrieval date"][:-1], axis=1)
    return data

def create_events(data: pd.DataFrame) -> pd.DataFrame:
    """
    Create an Event object for each bet.
    """
    
    data['Event'] = data.apply(lambda x: Event(x["Probability"], x["var2outcome"], [BetIdentifier(x["ID"], x["Bet type"], x["Bet type value"])], add_null_variable=True), axis=1)

    return data


def prepare_rows(data: pd.DataFrame) -> pd.DataFrame:
    data = filter_rows(data)
    data = change_dates_format(data)
    data = add_approximate_end_date(data)
    data = add_outcome_column(data)
    data = add_probability_column(data)

    return data

def rows_to_event_format(data: pd.DataFrame) -> pd.DataFrame:
    data = separate_bookmakers(data)
    data = filter_invalid_odds(data)
    data = add_var2outcome_column(data)
    data = add_bet_id_column(data)
    data = add_retrieval_batch_column(data)
    data = data.drop_duplicates(subset=["Bet ID", "Bookmaker", "Retrieval batch"])

    return data


def start(data: pd.DataFrame) -> pd.DataFrame:
    data = prepare_rows(data)
    data = rows_to_event_format(data)
    data = create_events(data)
    data = index_by(data, levels=["Retrieval date", "Bookmaker", "ID", "Bet type", "Bet type value"])
    data = sort_by_index(data, 'Retrieval date')

    return data
    