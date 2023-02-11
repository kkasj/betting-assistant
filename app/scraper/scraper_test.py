import numpy as np
import time
from datetime import datetime
from .scraper_flashscore import *
from .scraper_betexplorer import *
from .scraper_main import *


for elem in get_flashscore_odds(http_flashscore_odds('2TdgWEPK', 'soccer')):
    print(elem)
exit()
match_data = get_match_data(datetime.now())
# for elem in match_data:
#     print(elem)

df = pd.DataFrame(match_data)[['Link', 'Date']]
hour = df['Date'].apply(lambda x: int(x.split(',')[-2]))
minute = df['Date'].apply(lambda x: int(x.split(',')[-1]))

df = pd.concat([df, hour, minute], axis=1)
df.columns = ['Link', 'Date', 'Hour', 'Minute']

date = datetime.now()
df = df[(df["Hour"] > date.hour) | ((df["Hour"] == date.hour) & (df["Minute"] > date.minute))]


df = df.sort_values(['Hour', 'Minute'])
df = df.reset_index(drop=True)
df = df.iloc[:30]


print(df)
# print(len(match_data))
