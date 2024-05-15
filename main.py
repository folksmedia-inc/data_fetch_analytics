from fastapi import FastAPI, HTTPException
import csv
import aiohttp
from starlette.responses import Response
from fastapi import Depends
from config import tracker
import pymysql
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Accessing Analytics Backend Server"}


@app.get("/fetch_data")
async def fetch_data(
    root: str,
    exp: str,
    start_date: str,
    end_date: str,
    conn= Depends(tracker)
):
    """
    Fetches data from the specified URL and returns the response.

    Parameters:
    - root: str (required), e.g., "AAPL"
    - exp: str (required), e.g., "20231117"
    - start_date: str (required), e.g., "20231110"
    - end_date: str (required), e.g., "20231110"
    - right: str (required), e.g., "P" or "C"
    - ivl: int (optional, default=900000), e.g., 900000
    """
    connection, cur = conn
    exp_y = exp[:4]
    exp_m = exp[4:6]
    exp_d = exp[6:]
    expiration_date_formatted = f"{exp_y}-{exp_m}-{exp_d}"
    url = f"http://3.85.111.217:25510/v2/bulk_hist/option/open_interest?root={root}&exp={exp}&start_date={start_date}&end_date={end_date}&use_csv=true"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            table_name = 'open_interest'
            if response.status == 200:
                # create_or_update_table(table_name, conn)
                if response.content_type == "application/json":
                    data = await response.json()
                    return JSONResponse(content=data, status_code=200)
                else:
                    try:
                        csv_data = await response.text()
                        headers = {
                            "Content-Disposition": response.headers.get("Content-Disposition"),
                            "Content-Type": response.headers.get("Content-Type")
                        }
                        # Parse the CSV data
                        csv_rows = csv.reader(csv_data.splitlines())
                        next(csv_rows)  # Skip the header

                        connection.ping(reconnect=True)  # Ensure the connection is alive

                        with connection.cursor() as cur:

                            fetch_sql = f"""SELECT DISTINCT(date) AS date from open_interest WHERE ticker='{root}' AND expiration_date='{expiration_date_formatted}'"""
                            cur.execute(fetch_sql)
                            existing_dates = cur.fetchall()
                            existing_dates = [i["date"] for i in existing_dates] if existing_dates else []

                            for row in csv_rows:
                                ticker, expiration, strike, call_put, ms_of_day, open_interest, date = row

                                strike_updated = int(strike)/1000

                                date_y =date[:4]
                                date_m = date[4:6]
                                date_d = date[6:]
                                date_formatted = f"{date_y}-{date_m}-{date_d}"

                                if date_formatted in existing_dates:
                                    print(f'Not entering for {date_formatted} since it already exists')
                                    continue

                                sql = f"""INSERT INTO {table_name} 
                                            (ticker, expiration_date, strike, call_put, ms_of_day, open_interest, date) 
                                            VALUES (%s, %s, %s, %s, %s, %s, %s)"""
                                values = (ticker, expiration_date_formatted, strike_updated, call_put, ms_of_day, int(open_interest), date_formatted)

                                try:
                                    cur.execute(sql, values)
                                except pymysql.Error as e:
                                    raise HTTPException(detail=f"Error: {e}", status_code=400)

                            connection.commit()
                        return JSONResponse(content='Success', status_code=200)
                    except Exception as err:
                        import traceback
                        print(traceback.format_exc())
                        pass
            else:
                raise HTTPException(detail=f"Unexpected response: {response.status} ({response.reason})", status_code=400)
# fetch_data('SPWX', '20231103', '20231103', '20240511')