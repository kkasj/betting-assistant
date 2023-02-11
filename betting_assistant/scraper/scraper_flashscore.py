import pandas as pd
import numpy as np
import re
import requests
import concurrent.futures
from typing import List, Dict

from .aliases import *

session = requests.Session()


def get_flashscore_odds(http_response: str) -> dict:
    '''
    Processes scraped http response to provide odds in a list of dictionaries.
    '''

    match_id = http_response['match_id']
    text = http_response['text']
    sport = http_response['sport']

    matches = list(re.finditer(r"(.*?)~", text))

    class Node:
        def __init__(self, level, parent, label, value):
            self.children = []
            self.level = level
            self.parent = parent
            self.label = label
            self.value = value

    class Tree:
        def __init__(self):
            self.root = Node(-1, None, None, None)

        def addNode(self, level, label, value):
            c = self.root
            while len(c.children) > 0 and (c.children[0].level != level):
                c = c.children[-1]
            c.children.append(Node(level, c, label, value))
        
        @staticmethod
        def printableTree(root):
            if len(root.children) == 0:
                return []

            if root.children[0].level == 3: # compile odds
                return [[elem1 for elem1 in [root.label, root.value] if elem1 is not None] + elem for elem in [[{k.label: str(k.value) for k in root.children}]]]

            else:
                r = []

                for c in root.children:
                    r += [[elem1 for elem1 in [root.label, root.value] if elem1 is not None] + elem for elem in Tree.printableTree(c)]

                return r

        def printTree(self):
            for elem in Tree.printableTree(self.root):
                odds = elem.pop(-1)
                bet_data = {"Bet type": elem}
                bet_data.update(odds)
                print(bet_data)
        
        # clean branches with no odds
        @staticmethod
        def staticCleanTree(node):
            # check if leaf
            if len(node.children) == 0:
                if node.level != 3:
                    # prune single branch
                    while node.parent is not None and len(node.parent.children) == 1:
                        node = node.parent

                    if node.parent is not None:
                        p = node.parent
                        p.children.remove(node)
                    else:
                        node.children = []
            
            else:
                for c in node.children:
                    Tree.staticCleanTree(c)
        
        def cleanTree(self):
            Tree.staticCleanTree(self.root)
            
        def matchBets(self):
            match_bets = []

            for elem in Tree.printableTree(self.root):
                odds = elem.pop(-1)
                bet_data = {"Bet type": elem}
                bet_data.update(odds)
                match_bets.append(bet_data)
            
            return match_bets

        

    tree = Tree()

    for match in matches:
        d = {elem.group(1): elem.group(2) for elem in re.finditer(r"(.*?)÷(.*?)¬", match.group(1))}
        if 'OA' in d.keys():
            tree.addNode(0, d['OAI'], None)
        elif 'OB' in d.keys():
            tree.addNode(1, d['OBI'], None)
        elif 'OC' in d.keys():
            tree.addNode(2, None, d['OC'])
        elif 'OE' in d.keys() and d['OG']=='1':
            tree.addNode(3, d['OE'], [float(re.search(r"[.0-9]*$", val).group(0)) for key, val in d.items() if key[0] == 'X'])

    tree.cleanTree()

    # tree.printTree()

    match_bets = []

    for bet in tree.matchBets():
        bt_id = None

        if str(bet['Bet type']) in flashscore_aliases[sport].keys():
            bt_id = flashscore_aliases[sport][str(bet['Bet type'])]
            bet['Bet type value'] = np.nan
            bet['Bet type'] = bt_id

            found_duplicate = False
            for i, b in enumerate(match_bets):
                if b['Bet type'] == bet['Bet type'] and b['Bet type value'] == bet['Bet type value']:
                    found_duplicate = True
                    if len(bet.keys()) > len(b.keys()):
                        match_bets[i] = bet
                        break
            if not found_duplicate:
                match_bets.append(bet)

        elif str(bet['Bet type'][:-1]) in flashscore_aliases[sport].keys():
            bt_id = flashscore_aliases[sport][str(bet['Bet type'][:-1])]
            bet['Bet type value'] = float(bet['Bet type'][-1])
            bet['Bet type'] = bt_id
            match_bets.append(bet)
    
    return match_bets


def http_flashscore_odds(match_id: str, sport: str) -> dict:
    '''
    Request polish odds from flashscore.pl.
    
    Sends an http request to flashscore.pl to obtain polish odds for a match with 'match_id', playing 'sport'. 
    Returns a dictionary of three keys {"match_id", "text", "sport"}, where "text" is the text response of the site.
    '''

    url = "https://d.flashscore.pl/x/feed/df_od_1_" + match_id
    text = session.get(url, headers = {
                "authority": "d.flashscore.pl",
                "method": "GET",
                "path": "/x/feed/df_od_1_" + match_id,
                "scheme": "https",
                "referer": "https://www.google.com/",
                "accept": "*/*",
                "accept-encoding": "gzip, deflate, br",
                "accept-language": "pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7",
                "referer": "https://d.flashscore.pl/x/feed/proxy-fetch",
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-origin",
                "sec-gpc": "1",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36 OPR/89.0.4447.64",
                "x-fsign": "SW9D1eZo"
                }).text

    return {'match_id': match_id, 'text': text, 'sport': sport}



def scraper_flashscore(match_ids: List[str], sport: str) -> dict:
    '''
    Scrapes and compiles odds for every match in 'match_ids' playing 'sport'

    Uses 'http_flashscore_odds()' to get polish odds for every match in 'match_ids' playing 'sport'. 
    Then uses 'get_flashscore_odds()' to organize the odds into a dictionary {'match_id': 'odds'}, 
    where 'odds' is the dictionary returned by 'get_flashscore_odds()' for 'match_id'. 
    '''

    CONNECTIONS = 3

    flashscore_odds = dict()

    with concurrent.futures.ThreadPoolExecutor(CONNECTIONS) as executor:
        future_match_id = {executor.submit(http_flashscore_odds, match_id, sport): match_id for match_id in match_ids}

    for future in future_match_id:
        match_id = future_match_id[future]

        try:
            http_response = future.result()
        except Exception as exc:
            http_response = {'match_id': match_id, 'text': "", 'sport': sport}
        finally:
            flashscore_odds[match_id] = get_flashscore_odds(http_response)
            # print(match_id, "DONE")
    

    return flashscore_odds
