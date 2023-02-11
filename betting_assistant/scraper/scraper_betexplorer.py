from bs4 import BeautifulSoup
import numpy as np
import re
import requests
from datetime import datetime
from .aliases import *
import time
import concurrent.futures
import pandas as pd
from copy import deepcopy
from typing import List

session = requests.Session()

bookie_ids = [207, 1039, 11, 102, 147, 25, 148, 41, 43, 45, 241]
bookmakers = ['10Bet','1xBet','bet365','bet-at-home','BetVictor','Pinnacle','William Hill','Betway','Unibet','Interwetten','Betsson']

def http_match_data(betexplorer_link):
    '''
    OBSOLETE
    '''
    text = session.get(betexplorer_link, headers = {
            "authority": "www.betexplorer.com",
            "method": "GET",
            "path": betexplorer_link[betexplorer_link.index('/'):],
            "scheme": "https",
            "referer": "https://www.google.com/",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7",
            "sec-ch-ua": '"Opera GX";v="89", "Chromium";v="103", "_Not:A-Brand";v="24"',
            "sec-ch-ua-platform": "Windows",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36 OPR/89.0.4447.64",
        }).text
    
    match_data_soup = BeautifulSoup(text, 'lxml')

    return betexplorer_link, match_data_soup

def http_betexplorer_odds(betexplorer_link: str, bet_type: str) -> tuple:
    '''
    Request odds from betexplorer.com
    
    Sends an http request to betexplorer.com to obtain polish 'bet_type' odds for a match on 'betexplorer_link'. 
    Returns a tuple of three elements ("match_id", "bet_type", "odds_soup"), where "odds_soup" is the text response of the site.
    '''

    match_id = betexplorer_link[-9:-1]
    url = 'https://www.betexplorer.com/match-odds/' + match_id + '/0/' + bet_type + '/'

    text = session.get(url, headers = {
            "authority": "www.betexplorer.com",
            "method": "GET",
            "path": "/match-odds/" + match_id + "/0/" + bet_type + "/",
            "scheme": "https",
            "referer": "https://www.google.com/",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7",
            "sec-ch-ua": '"Opera GX";v="89", "Chromium";v="103", "_Not:A-Brand";v="24"',
            "sec-ch-ua-platform": "Windows",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36 OPR/89.0.4447.64",
            "x-requested-with": "XMLHttpRequest",
        }).text.replace("\\", "")


    odds_soup = BeautifulSoup(text, 'lxml')

    return match_id, bet_type, odds_soup
    


def get_betexplorer_odds(http_response: str, bt_values: List[int]) -> dict: # bet type values
    '''
    Processes scraped http response from betexplorer to provide a list of dictionaries of odds for a given match, bet type and bet type values (bet type arguments)
    '''

    match_id, bet_type, soup = http_response
    d = datetime.now()
    retrieval_date = '{d.day},{d.month},{d.year},{d.hour}'.format(d = d) + d.strftime(",%M")
    no_val = np.any(pd.isnull(bt_values))
    bt_values = [str(val) for val in bt_values]



    div = soup.select_one('tr:has(> th[class="table-main__detail-odds"])')
    if div is not None:
        n_outcomes = len(div.select('th[class="table-main__detail-odds"]'))
    else:
        n_outcomes = 0 # we won't be able to fetch odds

    

    bets = {val: {"ID": match_id, "Retrieval date": retrieval_date} for val in bt_values}


    if no_val:
        for bookie_id in bookie_ids:
            a = soup.select_one("tr:has(> td:has(> a[data-bid='" + str(bookie_id) + "']))")

            if a is None:
                continue
            
            b = a.select('td[data-odd]:not(.inactive)')

            if b is None or len(b) != n_outcomes:
                continue

            bets[str(np.nan)][str(bookie_id)] = str([float(elem_odds['data-odd']) for elem_odds in b])

    else:
        for bookie_id in bookie_ids:
            a = soup.select("tr:has(> td:has(> a[data-bid='" + str(bookie_id) + "']))")

            if a is None or a == []:
                continue
            
            for tr in a:
                val = tr.select_one('td[class="table-main__doubleparameter"]')
                if val is None:
                    continue
                val = val.text

                try:
                    val = str(float(val))
                except:
                    continue

                if val not in bt_values:
                    continue
                
                b = tr.select('td[data-odd]:not(.inactive)')

                if b is None or len(b) != n_outcomes:
                    continue

                bets[str(val)][str(bookie_id)] = str([float(elem_odds['data-odd']) for elem_odds in b])


    return bets



    
def scraper_betexplorer(match_ids: list, betexplorer_links: dict, flashscore_odds: dict, match_bet_types: dict, sports: list) -> list:
    '''
    Appends flashscore-scraped polish odds by odds from betexplorer for matches in 'match_ids' playing 'sport'

    Returns a list of bets.
    '''
    CONNECTIONS = 6

    all_bets = []

    # add all matches and their corresponding bet types to the executor
    with concurrent.futures.ThreadPoolExecutor(CONNECTIONS) as executor:
        future_match_id = {executor.submit(http_betexplorer_odds, betexplorer_links[match_id], betexplorer_aliases[bt]): {'match_id': match_id, 'bt': bt} for sport in sports for match_id in match_ids[sport] for bt in match_bet_types[match_id]}


    for future in concurrent.futures.as_completed(future_match_id):
        match_id = future_match_id[future]['match_id']
        bt = future_match_id[future]['bt'] # bet type
        try:
            http_response = future.result()
        except:
            continue
        finally:
            bt_values = [bet['Bet type value'] for bet in flashscore_odds[match_id] if bet['Bet type'] == bt]

            bets = get_betexplorer_odds(http_response, bt_values)

            for bet in flashscore_odds[match_id]:
                if bt != bet['Bet type'] or str(bet['Bet type value']) not in bets.keys():
                    continue

                bet.update(bets[str(bet['Bet type value'])])

                if '25' in bet.keys() and not np.any(pd.isnull(bet['25'])): # make sure there are pinnacle odds for this bet
                    all_bets.append(bet)


    
    return all_bets
