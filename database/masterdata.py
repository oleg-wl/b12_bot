from datetime import datetime, timedelta

import polars as pl

from tools import DB_Admin

def insert_master_table():

    seats = ["2B.{:0>3}".format(i) for i in range(1, 23)]

    today = datetime.today()
    date_list = [today + timedelta(days=i) for i in range(365)]
    df = (
        pl.DataFrame({"dates": date_list})
        .join(pl.DataFrame({"seat": seats}), how="cross")
        .with_column(pl.lit(value=None, dtype=pl.Float32).alias('user_id'))
        .cast({"dates": pl.Date})
        .write_database(table_name="mastertable", connection=DB_Admin().engine.connect(), if_table_exists='replace')
    )


if __name__ == "__main__":
    insert_master_table()
