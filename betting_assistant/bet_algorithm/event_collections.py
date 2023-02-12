import pandas as pd
import numpy as np
from typing import List
from collections import defaultdict

from .events import Event, MultiEvent
from .utils import latest_date_str
from .bet_identifier import BetIdentifier
from . import preprocessing


class GenericEventCollection:
    def get_event_df(self) -> pd.DataFrame: # abstract
        # event_df is required to have:
        # columns "Event", "Outcome", "End date" 
        # index level "Retrieval date"
        raise NotImplementedError

    def set_event_df(self, event_df): # abstract
        raise NotImplementedError


    def calculate_bet_sizes(self):
        self.get_event_df()["Event"].apply(lambda x: x.calculate_bet_size())

    def filter_zero_bet_size(self):
        total_bet_size = self.get_event_df()["Event"].apply(lambda x: x.s.sum() != 0)
        self.set_event_df(self.get_event_df()[total_bet_size])

    def _util_overlap_utility(self, event_df: pd.DataFrame):
        # two types of action: making a bet, and evaluating a bet after the event has ended
        actions_bet = event_df.copy()
        actions_bet["Action"] = "Bet"
        actions_bet["Date spec"] = actions_bet.index.get_level_values('Retrieval date')

        actions_eval = event_df.copy()
        actions_eval["Action"] = "Evaluation"
        actions_eval["Date spec"] = actions_eval["End date"]

        actions = pd.concat([actions_bet, actions_eval], axis=0)
        actions = preprocessing.sort_by_column(actions, "Date spec")


        budget = 1.0
        current_bet_count = 0
        bet_id_map_event = defaultdict(list)
        DEBUG = True
        MAX_ENTANGLED = 20
        def handle_row(row):
            nonlocal budget, bet_id_map_event, current_bet_count
            action = row["Action"]

            if action == "Bet" and budget < 0.0001:
                row["Event"].replaced = True

            elif action == "Bet":
                event = row["Event"]
                event.replaced = False
                event.retrieval_budget = budget
                bet_id = event.bet_id

                events_with_common_bet_id = set()
                for bid in bet_id:
                    for e in bet_id_map_event[bid]:
                        if len(events_with_common_bet_id) == MAX_ENTANGLED:
                            break
                        events_with_common_bet_id.add(e)

                event.calculate_entangled_bet_size(ongoing_events=list(events_with_common_bet_id)[:4])

                if event.s.sum() > 0:
                    current_bet_count += 1
                    for bid in bet_id:
                        bet_id_map_event[bid].append(event)
                    budget -= np.sum(event.s) * event.retrieval_budget
                    if DEBUG:
                        print("budget:", budget)
                        print("bet")
                        print(current_bet_count, "bets remaining")
                else:
                    event.replaced = True
                

            elif action == "Evaluation" and not row["Event"].replaced:
                event = row["Event"]
                outcomes = row["Outcome"]
                if DEBUG:
                    print('budget:', budget)
                    print("evaluation")
                    print(current_bet_count, "bets remaining")
                current_bet_count -= 1
                bet_id = event.bet_id
                for bid in bet_id:
                    bet_id_map_event[bid].remove(event)
                budget += event.total_return(outcomes)

        actions.apply(handle_row, axis=1)

        return budget

    def overlap_utility(self):
        """
        Utility for event collection where events overlap in time.
        """
        
        events_df: pd.DataFrame = self.get_event_df().copy()

        return self._util_overlap_utility(events_df)

    def overlap_utility_grouped_by_day(self):
        """
        Utility for event collection where events overlap in time, grouped by day of retrieval.
        """

        event_df: pd.DataFrame = self.get_event_df().copy()
        event_df["Day"] = event_df.apply(lambda x: ','.join(x.name[0].split(',')[:3]), axis=1)

        grouped = event_df.groupby(["Day"])
        utilities = grouped.apply(self._util_overlap_utility)

        return utilities
        


    def expected_utility(self):
        ex_utility = self.get_event_df()["Event"].apply(lambda event: event.keu)

        return ex_utility.sum()
    
    def utility(self):
        u = self.get_event_df().apply(lambda x: x["Event"].log_utility(x["Outcome"]), axis=1)

        return u.sum()

        
    def expected_utility_grouped_by_day(self):
        event_df: pd.DataFrame = self.get_event_df().copy()
        event_df["Day"] = event_df.apply(lambda x: ','.join(x.name[0].split(',')[:3]), axis=1)
        event_df["Expected utility"] = event_df["Event"].apply(lambda event: event.keu)

        return event_df.groupby(["Day"])["Expected utility"].sum()

    def utility_grouped_by_day(self):
        event_df: pd.DataFrame = self.get_event_df().copy()
        event_df["Day"] = event_df.apply(lambda x: ','.join(x.name[0].split(',')[:3]), axis=1)
        event_df["Utility"] = event_df.apply(lambda x: x["Event"].log_utility(x["Outcome"]), axis=1)

        return event_df.groupby(["Day"])["Utility"].sum()


class EventCollection(GenericEventCollection):
    def __init__(self, event_df: pd.DataFrame):
        self.event_df = event_df

    @classmethod
    def from_event_dataframe(cls, event_df: pd.DataFrame):
        return cls(event_df)
    

    def get_event_df(self):
        return self.event_df

    def set_event_df(self, event_df):
        self.event_df = event_df


class MultiEventCollection(GenericEventCollection):
    def __init__(self, event_collection: EventCollection, k: int):
        self.multi_event_df = self.group_events(event_collection, k)

    @classmethod
    def from_event_collection(cls, event_collection: EventCollection, k: int):
        return cls(event_collection, k)
    
    @classmethod
    def from_event_dataframe(cls, events_df: pd.DataFrame, k: int):
        event_collection = EventCollection(events_df)
        return cls(event_collection, k)

    def get_event_df(self):
        return self.multi_event_df
    
    def set_event_df(self, multi_event_df):
        self.multi_event_df = multi_event_df


    def combine_grouped_events(self, rows: pd.DataFrame) -> pd.DataFrame:
        multi_event = MultiEvent.from_series(rows["Event"])
        new_row = pd.DataFrame({"Event": [multi_event], "Outcome": [rows["Outcome"].tolist()], "End date": [latest_date_str(rows["End date"].tolist())]})

        return new_row

    def group_events(self, event_collection: EventCollection, k: int): # k - number of events in a MultiEvent
        event_df = event_collection.event_df.copy()

        event_df['Subgroup spec'] = event_df.groupby(level=["Retrieval date", "Bookmaker"]).cumcount()
        event_df['Subgroup spec'] = event_df['Subgroup spec'].apply(lambda x: (x - (x%k)) // k)

        grouped = event_df.groupby([pd.Grouper(level="Retrieval date"), pd.Grouper(level="Bookmaker"), "Subgroup spec"])

        multi_event_df = grouped.apply(lambda x: self.combine_grouped_events(x))
        multi_event_df.index = multi_event_df.index.droplevel(-1) # remove useless indexing from combining grouped events

        return multi_event_df
