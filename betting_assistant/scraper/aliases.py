sports = ['soccer', 'basketball', 'hockey', 'tennis', 'baseball', 'volleyball', 'handball']

polish_bks = [163, 165, 539, 572, 569, 591, 472]
foreign_bks = [207, 1039, 11, 102, 147, 25, 148, 41, 43, 45, 241, 502]
bks = polish_bks+foreign_bks

flashscore_aliases = {
"soccer": 
{
    str(['1x2', 'ft']): 1,
    str(['1x2', 'ft-include-ot']): 1,
    str(['under-over', 'ft']): 2,
    str(['under-over', 'ft-include-ot']): 2,
    str(['moneyline', 'ft']): 3,
    str(['moneyline', 'ft-include-ot']): 3,
    str(['asian-handicap', 'ft']): 4,
    str(['asian-handicap', 'ft-include-ot']): 4,
    str(['double-chance', 'ft']): 5,
    str(['double-chance', 'ft-include-ot']): 5,
    str(['both-teams-to-score', 'ft']): 6,
    str(['both-teams-to-score', 'ft-include-ot']): 6,
},
"basketball":
{
    str(['1x2', 'ft']): 1,
    str(['1x2', 'ft-include-ot']): 1,
    str(['under-over', 'ft']): 2,
    str(['under-over', 'ft-include-ot']): 2,
    str(['moneyline', 'ft']): 3,
    str(['moneyline', 'ft-include-ot']): 3,
    str(['asian-handicap', 'ft']): 4,
    str(['asian-handicap', 'ft-include-ot']): 4,
    str(['double-chance', 'ft']): 5,
    str(['double-chance', 'ft-include-ot']): 5,
},
"hockey":
{
    str(['1x2', 'ft']): 1,
    str(['1x2', 'ft-include-ot']): 1,
    str(['under-over', 'ft']): 2,
    str(['under-over', 'ft-include-ot']): 2,
    str(['moneyline', 'ft']): 3,
    str(['moneyline', 'ft-include-ot']): 3,
    str(['asian-handicap', 'ft']): 4,
    str(['asian-handicap', 'ft-include-ot']): 4,
    str(['double-chance', 'ft']): 5,
    str(['double-chance', 'ft-include-ot']): 5,
    str(['both-teams-to-score', 'ft']): 6,
    str(['both-teams-to-score', 'ft-include-ot']): 6,
},
"tennis":
{
    str(['under-over', 'ft']): 2,
    str(['under-over', 'ft-include-ot']): 2,
    str(['moneyline', 'ft']): 3,
    str(['moneyline', 'ft-include-ot']): 3,
    str(['asian-handicap', 'ft']): 4,
    str(['asian-handicap', 'ft-include-ot']): 4,
},
"baseball":
{
    str(['under-over', 'ft']): 2,
    str(['under-over', 'ft-include-ot']): 2,
    str(['moneyline', 'ft']): 3,
    str(['moneyline', 'ft-include-ot']): 3,
    str(['asian-handicap', 'ft']): 4,
    str(['asian-handicap', 'ft-include-ot']): 4,
},
"volleyball":
{
    str(['under-over', 'ft']): 2,
    str(['under-over', 'ft-include-ot']): 2,
    str(['moneyline', 'ft']): 3,
    str(['moneyline', 'ft-include-ot']): 3,
    str(['asian-handicap', 'ft']): 4,
    str(['asian-handicap', 'ft-include-ot']): 4,
},
"handball":
{
    str(['1x2', 'ft']): 1,
    str(['1x2', 'ft-include-ot']): 1,
    str(['under-over', 'ft']): 2,
    str(['under-over', 'ft-include-ot']): 2,
    str(['asian-handicap', 'ft']): 4,
    str(['asian-handicap', 'ft-include-ot']): 4,
    str(['double-chance', 'ft']): 5,
    str(['double-chance', 'ft-include-ot']): 5,
}
}

betexplorer_aliases = {
    1: "1x2",
    2: "ou",
    3: "ha",
    4: "ah",
    5: "dc",
    6: "bts"
}

requires_value = {
    1: False,
    2: True,
    3: False,
    4: True,
    5: False,
    6: False
}