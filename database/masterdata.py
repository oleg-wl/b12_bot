from datetime import date
import hashlib

import pandas as pd
import requests

from source.exceptions import IncorrectPassword

class MasterTable:

    seats = None
    master_table = None

    def _make_seats_list(self):

        # собрать лист с рабочими местами
        # NOTE: кириллица
        self.seats = ["2В.{:0>3}".format(i) for i in range(1, 23)]
        self.seats.append("2А.001")
        self.seats.append("2А.002")

    def _make_weekends(self, year: int):
        r = requests.get(f"https://n01.isdayoff.ru/api/getdata?year={year}&cc=ru&pre=0")
        return [int(d) for d in r.text]

    def _make_calendar_list(self, year: int):
        # обьект календаря года с флагом 0 - рд/1 - вых
        year = int(year)
        weekend_days = self._make_weekends(year)

        start_day = date(year=year, month=1, day=1)
        end_day = date(year=year, month=12, day=31)

        period = pd.date_range(start=start_day, end=end_day, freq="D")

        df = pd.DataFrame(period, columns=["period_day"]).join(
            pd.DataFrame(weekend_days, columns=["is_weekend"]), how="left"
        )
        df.period_day = df.period_day.dt.date
        return df

    def make_table(self, start_y: int, end_y: int):
        try:
            int(start_y)
            int(end_y)
        except TypeError:
            print("Год должен быть интом")
        else:

            self._make_seats_list()

            self.master_table = pd.concat(
                [self._make_calendar_list(year=y) for y in range(start_y, end_y + 1)]
            ).join(pd.DataFrame(self.seats, columns=["seats"]), how="cross")

    @staticmethod
    def make_password(passwd):

        try:
            passwd = str(passwd).encode('utf-8')
        except:
            raise IncorrectPassword()
        else:
            p = hashlib.sha256()
            p.update(passwd)
            return p.hexdigest()

