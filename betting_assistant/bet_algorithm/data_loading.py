import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Optional

from .utils import datetime2str_dbformat
from ..scraper import scraper_main


scraper_package_path = '/'.join(scraper_main.__file__.split('\\')[-3:-1])

class Loader:
    """
    Generic data loader class
    """

    def __init__(self, days: List[str] | None = None):
        if days is None:
            days = [datetime2str_dbformat(datetime.now())]
    
        self.days = days
        self.odds = self._load_odds()
        self._prepare_odds()
        self.match_data = self._load_match_data()
        self.results = self._load_results()
        self.all_data = self._combine_odds_match_data()


    def _load_odds(self) -> pd.DataFrame: # abstract
        """
        Load odds
        """

        raise NotImplementedError
    
    def _load_match_data(self) -> pd.DataFrame:
        """
        Load match data from the database
        """

        dfs = []
        for day in self.days:
            try:
                match_data = pd.read_csv(scraper_package_path + '/data/match_data/' + day + '.csv')
                match_data.index = match_data["ID"]
                match_data = match_data.drop(columns=["ID"])

                dfs.append(match_data)
            except FileNotFoundError:
                pass

        match_data = pd.DataFrame() if len(dfs) == 0 else pd.concat(dfs, axis=0)
        match_data = match_data[~match_data.index.duplicated(keep='first')]

        return match_data
    
    def _load_results(self) -> pd.DataFrame:
        """
        Load results from the database
        """

        dfs = []
        for day in self.days:
            try:
                results = pd.read_csv(scraper_package_path + '/data/results/' + day + '.csv')
                results.index = results["ID"]
                results = results.drop(columns=["ID"])

                dfs.append(results)
            except FileNotFoundError:
                pass

        results = pd.DataFrame() if len(dfs) == 0 else pd.concat(dfs, axis=0)
        results = results[~results.index.duplicated(keep='first')]

        return results

    def _prepare_odds(self) -> pd.DataFrame:
        """
        Return an organized DataFrame with odds
        """    

        if self.odds.empty:
            return

        # clean the dataframe; drop rows with no ID
        self.odds = self.odds.dropna(subset=["ID"])


        # rearrange columns in odds dataframe
        cols = self.odds.columns.tolist()
        first_cols = ['ID', 'Retrieval date', 'Bet type', 'Bet type value']
        for col in first_cols:
            cols.remove(col)
        cols = first_cols + cols
        self.odds = self.odds[cols]


        # changing csv's str format to python list
        for col in self.odds.columns.tolist()[4:]:
            self.odds[col] = self.odds[col].apply(lambda x: np.nan if np.any(pd.isnull(x)) else [float(elem) for elem in x[1:-1].split(', ')])


    def _combine_odds_match_data(self) -> pd.DataFrame:
        """
        Merge 'odds' and 'match_data' dataframes into a single dataframe ['Date', 'Result', 'Partial results', 'ID', 'Retrieval date', <odds>]
        """

        # if there are no odds, return an empty dataframe
        if self.odds.empty:
            return pd.DataFrame()

        def get_date(id):
            try:
                return self.match_data.loc[id]["Date"]
            except:
                return np.nan
        
        def get_result(id):
            try:
                return self.results.loc[id]["Result"]
            except:
                return np.nan

        def get_partial_results(id):
            try:
                return self.results.loc[id]["Partial results"]
            except:
                return np.nan


        dates = self.odds["ID"].apply(get_date)
        results_raw = self.odds["ID"].apply(get_result)
        results = results_raw.apply(lambda x: np.nan if np.any(pd.isnull(x)) else [int(elem) for elem in x[1:-1].split(', ')])
        partial_results_raw = self.odds["ID"].apply(get_partial_results)
        partial_results = partial_results_raw.apply(lambda x: np.nan if np.any(pd.isnull(x)) else [[int(elem1) for elem1 in elem[1:].split(', ')] for elem in x[1:-2].split('], ')])


        data = pd.DataFrame()
        data["Date"] = dates
        data["Result"] = results
        data["Partial results"] = partial_results

        data = pd.concat([data, self.odds], axis=1)

        # drop rows with no date (=> no match data data for the given match)
        data = data.dropna(subset=["Date"])

        return data


class DBLoader(Loader):
    """
    Loader class for loading data from the database.

    Mainly used to evaluate betting strategies (bet size model + probability model) for past matches,
    for which we have results.
    """


    def _load_odds(self) -> pd.DataFrame:
        """
        Load odds from database
        """

        dfs = []
        for day in self.days:
            try:
                odds = pd.read_csv(scraper_package_path + '/data/odds/' + day + '.csv')

                dfs.append(odds)
            except FileNotFoundError:
                pass

        odds = pd.DataFrame() if len(dfs) == 0 else pd.concat(dfs, axis=0, ignore_index=True)
        
        return odds


class ScraperDataLoader(Loader):
    """
    Loader class for loading data directly from the scraper.

    Mainly used to predict future match outcome probabilities and determine optimal bet size. 
    """

    def _load_odds(self) -> pd.DataFrame:
        """
        Load odds directly from the scraper
        """

        odds_list = scraper_main.scraper_runner(max = 5)
        return pd.DataFrame(odds_list)
