from datetime import datetime

def date2str(d):
        return f"{d.year}_{d.month}_{d.day}"

def str2date(datestr):
    year, month, day = [int(elem) for elem in datestr.split('_')]
    date = datetime(year=year, month=month, day=day)

    return date

def datecomp(date1, date2):
    date1 = [int(elem) for elem in date1.split(',')]
    date2 = [int(elem) for elem in date2.split(',')]

    return date1>date2
