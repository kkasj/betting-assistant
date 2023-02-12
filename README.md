# Betting Assistant
A project aiming to provide an assistant tool for sports betting. It is not supposed to make betting decisions for you, but it will give you better advice than most tipsters out there.

## Dependencies
```pip install -r requirements.txt```

## Code example
### Using built-in odds data to test k-event combination bets overlapping in time
```python3
import pandas as pd

import betting_assistant.bet_algorithm.data_loading as data_loading
import betting_assistant.bet_algorithm.preprocessing as preprocessing
import betting_assistant.bet_algorithm.event_collections as event_collections
import betting_assistant.bet_algorithm.utils as utils

k = 2
START_DATE = '2022_9_8'
END_DATE = '2022_9_11'
days_list = utils.days_list_dbformat(START_DATE, END_DATE)

# load data from the database
loader = data_loading.DBLoader(days=days_list)
event_df = loader.all_data

# preprocess
event_df = preprocessing.start(events_df)

# create a multi-event collection, which is a collection of events with k-event combination bet variables
me = event_collections.MultiEventCollection.from_event_dataframe(event_df, k)

# calculate utility function separately for each day
utility_by_day = me.overlap_utility_grouped_by_day()

# or, if you wish, calculate the aggregate utility function across all days
agg_utility = me.overlap_utility()

print(utility_by_day)
print(agg_utility)
```

## How it works
If you are a bettor, all you need to do is to feed the tool with bet type and odds. What kind of odds? That is up to you.

Because of how its business model works, typically the best odds come from bookmaker Pinnacle. This is also why working with Pinnacle odds (whether you actually bet on them or just feed the Assistant) will give you the best profit in the long run.

After you give it the odds and type of each available bet you want to process, the Assistant will do the following:
* prepare the data for manipulation,
* extract probabilities of each possible outcome,
* use the Event-Utility framework to calculate optimal bet size,
* return the suggested sizes of bets as a fraction of the budget at your disposal.

## Why it works
Most methods for systematic winning in sports betting are based upon bet *value*, which is a fancy alias for the criterion $$\text{probability} \times \text{odds} > 1,$$ which basically serves as an elementary filtering device, leaving only profitable bets. To determine the bet size, they strive to maximize the expected value of a simple logarithmic [utility function](https://en.wikipedia.org/wiki/Utility). For example, a simple 1x2 bet has expected utility: $$E(u(s_1, s_2, s_3)) = \sum_{i=1}^{n} p_i\cdot \log(1+c_i\cdot s_i - (s_1 + s_2 + s_3))$$

The betting algorithm implemented in the Assistant generalizes that idea for:
* arbitrary bet structure (winning bet variable-to-outcome matrix),
* multiple bets at the same time,
* bets overlapping in time,
* multiple combination bets with shared events

to provide the most accurate mathematical model of player's bet portfolio.


## TODO
* user-friendly interface
* more elaborate code documentation
* better exception handling
* more usage examples
