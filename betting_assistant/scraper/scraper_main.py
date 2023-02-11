import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time
import requests
import pickle
import re
from .scraper_flashscore import scraper_flashscore
from .scraper_betexplorer import scraper_betexplorer
from .aliases import *
from .utils import *

module_path = '/'.join(__file__.split('/')[:-1])

def get_match_data(d):
    '''
    OBSOLETE
    '''

    # d = datetime.now()
    # tomorrow = d + timedelta(days=1)
    start_links = {}
    match_data = []

    for sport in sports:
        start_links[sport] = [f"https://www.betexplorer.com/next/{sport}/?year={d.strftime('%Y')}&month={d.strftime('%m')}&day={d.strftime('%d')}",]
                            # f"https://www.betexplorer.com/next/{sport}/?year={tomorrow.strftime('%Y')}&month={tomorrow.strftime('%m')}&day={tomorrow.strftime('%d')}"]


    for sport, start_links_ in start_links.items():
        for i, start_link in enumerate(start_links_):
            h = requests.get(start_link, headers = {
            "authority": "www.betexplorer.com",
            "method": "GET",
            "path": start_link[start_link.find("/next"):],
            "scheme": "https",
            "referer": "https://www.google.com/",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7",
            "sec-ch-ua": '"Opera GX";v="89", "Chromium";v="103", "_Not:A-Brand";v="24"',
            "sec-ch-ua-platform": "Windows",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36 OPR/89.0.4447.64",
            }).text

            soup = BeautifulSoup(h, 'lxml')

            table = soup.select_one('div[id="nr-ko-all"]')

            if table is None:
                continue

            matches = table.select('tr:has(> td:has(a[href="javascript:void(0);"]))')

            if matches is None:
                continue

            for match in matches:
                link = match.select_one('a[href]')['href']
                if link[:len(sport)+1] != '/'+sport:
                    continue
                link = "https://www.betexplorer.com" + link

                match_id = link[-9:-1]
                country = re.search(f"{sport}/([^/]*)/", link).group(1)
                league = re.search(f"{country}/([^/]*)/", link).group(1)

                try:
                    time = match.select_one('span[class="table-main__time"]').text.split(':')
                    hour = str(int(time[0]))
                    minute = time[1]
                    d1 = d + timedelta(days=i)
                    date = f"{d1.year},{d1.month},{d1.day},{hour},{minute}"
                except:
                    date = np.nan

                match_data.append({"ID": match_id, "Link": link, "Date": date, "Sport": sport, "Country": country, "League": league})

    return match_data

def get_results(datestr):
    d = str2date(datestr)
    start_links = {}
    results = []

    for sport in sports:
        start_links[sport] = [f"https://www.betexplorer.com/results/{sport}/?year={d.strftime('%Y')}&month={d.strftime('%m')}&day={d.strftime('%d')}"]


    for sport, start_links_ in start_links.items():
        for start_link in start_links_:
            h = requests.get(start_link, headers = {
            "authority": "www.betexplorer.com",
            "method": "GET",
            "path": start_link[start_link.find("/next"):],
            "scheme": "https",
            "referer": "https://www.google.com/",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7",
            "sec-ch-ua": '"Opera GX";v="89", "Chromium";v="103", "_Not:A-Brand";v="24"',
            "sec-ch-ua-platform": "Windows",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36 OPR/89.0.4447.64",
            }).text

            soup = BeautifulSoup(h, 'lxml')

            table = soup.select_one('div[id="nr-all"]')

            if table is None:
                continue

            matches = table.select('tr:has(> td[class="table-main__result"])')

            if matches is None:
                continue

            for match in matches:
                link = match.select_one('a[href]')['href']
                if link[:len(sport)+1] != '/'+sport:
                    continue
                link = "https://www.betexplorer.com" + link

                match_id = link[-9:-1]

                try:
                    result = match.select_one('td[class="table-main__result"]')
                    result = None if result is None else result.select_one('strong')
                    result = None if result is None else result.text
                    result = np.nan if result is None else str([int(elem) for elem in result.split(':')])
                except:
                    result = np.nan

                try:
                    partial_results = match.select_one('td[class="table-main__partial"]')
                    partial_results = None if partial_results is None else partial_results.text
                    partial_results = np.nan if partial_results is None else str([[int(elem1) for elem1 in elem.split(':')] for elem in partial_results[1:-1].split(', ')])
                except:
                    partial_results = np.nan


                results.append({"ID": match_id, "Result": result, "Partial results": partial_results})

    return results

def load_match_links(max = 200):
    '''
    Scrapes links and match info for 'max' matches on betexplorer.com and saves them in the database  

    Returns the links in the form of a dictionary {sport: links for matches in sport}.
    '''

    date = datetime.now()
    tomorrow = date + timedelta(days=1)
    d = date2str(date)  # today's date in str format
    d2 = date2str(tomorrow) # tomorrow's date in str format

    # try to load match data dataframe for today
    try:
        df = pd.read_csv(module_path + '/data/match_data/' + d + '.csv')
        df = df[['Link', 'Date', 'Sport']]
    # if there isn't one in our database, fetch it from the site
    except:
        match_data = get_match_data(date)
        save_data(match_data, module_path + '/data/match_data/')
        df = pd.DataFrame(match_data)[['Link', 'Date', 'Sport']]

        # denote that there are pending results for this day
        try:
            pending_results = pd.read_csv(module_path + '/data/pending_results.csv', header=None)
            # to series
            pending_results = pending_results.iloc[:, 0]
        except:
            pending_results = pd.Series(dtype='object')
        
        pending_results = pd.concat([pending_results, pd.Series([d], dtype='object')])
        pending_results.to_csv(module_path + '/data/pending_results.csv', index=False, header=False)
    
    # try to load match data dataframe for tomorrow
    try:
        df2 = pd.read_csv(module_path + '/data/match_data/' + d2 + '.csv')
        df2 = df2[['Link', 'Date', 'Sport']]

        # append
        df = pd.concat([df, df2], ignore_index=True)
    # if there isn't one in our database, fetch it from the site
    except:
        match_data = get_match_data(tomorrow)
        save_data(match_data, module_path + '/data/match_data/', tomorrow)
        df2 = pd.DataFrame(match_data)[['Link', 'Date', 'Sport']]

        # append
        df = pd.concat([df, df2], ignore_index=True)

        # denote that there are pending results for this day
        try:
            pending_results = pd.read_csv(module_path + '/data/pending_results.csv', header=None)
            # to series
            pending_results = pending_results.iloc[:, 0]
        except:
            pending_results = pd.Series(dtype='object')
        
        pending_results = pd.concat([pending_results, pd.Series([d2], dtype='object')])
        pending_results.to_csv(module_path + '/data/pending_results.csv', index=False, header=False)

    
    if df.empty:
        return {sport: [] for sport in sports} # empty match links dict

    # adding superficial columns serving as sorting keys
    datekey = df['Date'].apply(lambda x: [int(elem) for elem in x.split(',')])
    df = pd.concat([df, datekey], axis=1)
    df.columns = ['Link', 'Date', 'Sport', 'Datekey']

    # do not include past matches
    df = df[df['Datekey'].apply(lambda x: x>[date.year, date.month, date.day, date.hour, date.minute])]
    # sort by date
    df = df.sort_values(['Datekey'])
    # reset index
    df = df.reset_index(drop=True)
    # fetch only first 'max' matches
    df = df.iloc[:max]



    # prepare the match links format {sport: [match links for that sport]}
    match_links = dict()
    for sport in sports:
        match_links[sport] = df[df["Sport"] == sport]['Link'].tolist()


    return match_links

def scrape_matches(match_links: dict) -> list:
    '''
    Scrapes matches in 'match_links'
    '''

    # create match_ids and betexplorer_links dictionaries:
    # match_ids = {sport: list of match ids}
    # betexplorer_links = {match id: betexplorer link}
    match_ids = dict()
    betexplorer_links = dict()
    for sport in sports:
        match_ids[sport] = [elem[-9:-1] for elem in match_links[sport]]
        for elem in match_links[sport]:
            betexplorer_links[elem[-9:-1]] = elem


    # craate a dictionary of flashscore odds
    flashscore_odds = dict()
    for sport in sports:
        flashscore_odds.update(scraper_flashscore(match_ids[sport], sport))
    print("DONE FLASHSCORE")

    match_bet_types = dict() # bet types scraped from flashscore for each match 
    for sport in sports:
        for match_id in match_ids[sport]:
            match_bet_types[match_id] = list(set([elem['Bet type'] for elem in flashscore_odds[match_id]]))

    # append the dictionary of flashscore odds by the odds scraped from betexplorer
    all_bets = scraper_betexplorer(match_ids, betexplorer_links, flashscore_odds, match_bet_types, sports)
    print("DONE BETEXPLORER")
    
    return all_bets

def save_data(data, save_path = module_path + '/data/', date = None) -> None:
    '''
    Saves 'data' to 'save_path' in a csv file named 'Y_M_D.csv'

    For the function to work properly, 'data' must be convertible to a pandas DataFrame.
    '''

    if date is None: # if no date is given
        date = datetime.now()

    def load_csv():
        try:
            return pd.read_csv(save_path+date2str(date)+'.csv')
        except:
            return pd.DataFrame()
    
    def save_csv(df):
        # avoid any errors when df is empty
        if not df.empty:
            df.to_csv(save_path+date2str(date)+'.csv', index=False)

    # append odds to the existing file / create new file
    df = load_csv()
    app_df = pd.DataFrame(data) # dataframe to be appended
    df = pd.concat([df, app_df])
    save_csv(df)

def fill_pending_results():
    date = datetime.now()
    try:
        pending_results = pd.read_csv(module_path + '/data/pending_results.csv', header=None)

        # sort by date
        pending_results.columns = ['A']
        pending_results['Date'] = pending_results['A'].apply(lambda x: [int(elem) for elem in x.split('_')])
        pending_results = pending_results.sort_values('Date')

        # to list
        pending_results = pending_results.iloc[:, 0].tolist()

        pending_results1 = pending_results
        pending_results = [elem for elem in pending_results if datetime(*[int(elem1) for elem1 in elem.split('_')])+timedelta(days=1, hours=6) < date]
        pending_results1 = [elem for elem in pending_results1 if elem not in pending_results]
    except:
        return
    
    print("##### STARTED FILLING PENDING RESULTS; DO NOT EXIT")
    for datestr in pending_results[:3]:
        results = get_results(datestr)
        save_data(results, module_path + '/data/results/', str2date(datestr))
    pending_results = pending_results[3:] + pending_results1 # delete fetched results from the pending list
    
    pd.Series(pending_results, dtype='object').to_csv(module_path + '/data/pending_results.csv', index=False, header=False)
    print("##### FINISHED FILLING PENDING RESULTS")


def scrape(max = 200) -> list:
    '''
    Scrapes 'max' matches and returns compiled odds
    '''

    match_links = load_match_links(max)

    time1 = time.time()
    print("STARTED SCRAPING")
    bets = scrape_matches(match_links) # scraping
    time2 = time.time()

    # OPTIONAL: save the scraped data
    # save_bets(bets, 'scrape/data/odds/')

    print(f"{datetime.now()}: SCRAPED {len(bets)} BETS IN {int((time2-time1)/60)} minutes {int(60*((time2-time1)/60 - int((time2-time1)/60)))} seconds")
    # fill_pending_results()

    return bets

def loop(max = 200):
    while True:
        schedule = [1, 31]

        minute = datetime.now().minute
        sleep_times = [((schedule_minute - minute - 1) % 60) + 1 for schedule_minute in schedule]
        sleep_time = min(sleep_times) # in minutes

        time.sleep(sleep_time * 60)

        scrape(max)
        

def scraper_runner(max = 150):
    return scrape(max)

        
if __name__ == "__main__":
    # pass
    # scrape(max = 150)
    loop(max = 150)

