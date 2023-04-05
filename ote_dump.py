#!/usr/bin/env python3
import sys
import numpy as np
import requests
import pandas as pd
from datetime import datetime, timedelta

OTE_DAILY_MARKET_URL = "https://www.ote-cr.cz/cs/kratkodobe-trhy/elektrina/denni-trh/@@chart-data?report_date={year:04d}-{month:02d}-{day:02d}"
CNB_EXCHANGE_RATE_URL = "http://www.cnb.cz/cs/financni-trhy/devizovy-trh/kurzy-devizoveho-trhu/kurzy-devizoveho-trhu/denni_kurz.txt?date={day:02d}.{month:02d}.{year:04d}"


def get_session(retries=10):
    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def get_exchange_rate(session, year, month, day, currency, url=CNB_EXCHANGE_RATE_URL):
    endpoint = url.format(year=year, month=month, day=day)
    response = session.get(endpoint)
    if response.status_code == 200:
        for line in response.text.split("\n"):
            columns = line.split("|")
            if len(columns) >= 5:
                symbol = columns[3]
                if symbol == currency:
                    amount = float(columns[2])
                    price = float(columns[4].replace(",", "."))
                    rate = price / amount
                    return rate
        print(f"Response from {endpoint} doesn't contain {currency}.")
    else:
        print(f"Failed to fetch data from {endpoint}.")

    return None


def point2prices(point, exchange_rate, title):
    if 'y' in point:
        price = point['y']
        if title == "Cena (EUR/MWh)":
            price_eur = price
            price_czk = price * exchange_rate
        elif title == "Cena (CZK/MWh)":
            price_czk = price
            price_eur = price / exchange_rate
        else:
            raise NotImplementedError(
                "Conversion to CZK and EUR is not implemented for \"{0}\"".format(title))
    else:
        price_czk = np.nan
        price_eur = np.nan

    return price_eur, price_czk


def dump_daily_data(session, year, month, day, url=OTE_DAILY_MARKET_URL):
    endpoint = url.format(year=year, month=month, day=day)
    response = session.get(endpoint)
    if response.status_code == 200:
        data = response.json()

        prices = {'year': [], 'month': [], 'day': [], 'hour': [], 'price_eur': [], 'price_czk': []}
        for data_line in data['data']['dataLine']:
            if data_line["title"].startswith("Cena"):
                exchange_rate = get_exchange_rate(session, year, month, day, 'EUR')
                for point in data_line['point']:
                    price_eur, price_czk = point2prices(point, exchange_rate, data_line["title"])
                    hour = point['x']
                    prices['year'].append(year)
                    prices['month'].append(month)
                    prices['day'].append(day)
                    prices['hour'].append(hour)
                    prices['price_eur'].append(price_eur)
                    prices['price_czk'].append(price_czk)

        df = pd.DataFrame(prices)
        return df
    else:
        print(f"Failed to fetch data from {endpoint}")
        return None


def save_df(df, fname, cur_date):
    df.astype({'year': 'int', 'month': 'int', 'day': 'int', 'hour': 'int'}).to_csv(fname, index=False)
    sys.stdout.write(f"Saved up to {cur_date.year:04d}-{cur_date.month:02d}-{cur_date.day:02d} ... {fname}\033[K\n")
    sys.stdout.flush()


def load_df(fname):
    try:
        df = pd.read_csv(fname)
        last_line = df.iloc[-1]
        next_date = datetime(year=int(last_line["year"]), month=int(last_line["month"]), day=int(last_line["day"])) + \
                    timedelta(days=1)
    except FileNotFoundError:
        df = None
        next_date = None

    return next_date, df


def dump_all_data(session, fname, start_date=None, end_date=None):

    day = timedelta(days=1)

    if start_date is None:
        start_date = datetime(year=2002, month=1, day=1)  # data in OTE starts at 2002-01-01
        # OTE switched to using EUR on 2009-02-01

    if end_date is None:
        end_date = datetime.now() + day

    last_saved_date = start_date

    complete_df = None

    cur_date, complete_df = load_df(fname)

    if cur_date is None:
        cur_date = start_date

    while cur_date < end_date:
        sys.stdout.write("Downloading ... {y:04d}-{m:02d}-{d:02d}\033[K\r".format(y=cur_date.year, m=cur_date.month, d=cur_date.day))
        daily_df = dump_daily_data(session, cur_date.year, cur_date.month, cur_date.day)
        if complete_df is not None:
            complete_df = pd.concat([complete_df, daily_df])
        else:
            complete_df = daily_df

        if (cur_date - last_saved_date) > timedelta(days=30):
            save_df(complete_df, fname, cur_date)
            last_saved_date = cur_date
        cur_date += day

    save_df(complete_df, fname, cur_date)


# 2009-02-01 is the date when OTE API started to serve prices in EUR
#dump_all_data('ote_prices.csv', start_date=datetime(year=2009, month=2, day=1))

session = get_session(retries=10)
dump_all_data(session, 'ote_prices.csv', start_date=datetime(year=2002, month=1, day=1))
