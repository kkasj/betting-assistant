import pandas as pd
from time import time

import betting_assistant.bet_algorithm.data_loading as data_loading
import betting_assistant.bet_algorithm.preprocessing as preprocessing
import betting_assistant.bet_algorithm.event_collections as event_collections
import betting_assistant.bet_algorithm.utils as utils


if __name__ == "__main__":
    pd.options.display.max_columns = 15

    t = time()

    loader = data_loading.DBLoader(days=['2022_9_28'])
    # loader = data_loading.DBLoader(days=utils.days_list_dbformat('2022_9_8', '2022_9_18'))

    events_df = loader.all_data
    # events_df = loader.all_data.iloc[:500]
    events_df = preprocessing.start(events_df)
    print(events_df)


    # e = event_collections.EventCollection(events_df)
    # print(e.expected_utility_grouped_by_day())
    # print(e.overlap_utility_grouped_by_day())


    me = event_collections.MultiEventCollection.from_event_dataframe(events_df, 2)
    # print(me.expected_utility_grouped_by_day())
    print(me.overlap_utility_grouped_by_day())
    # print(me.overlap_utility())

    t = time() - t
    print(f"{int(t//60)} mins {int(t - t//60*60)} secs")