from fastapi import FastAPI
import json
import csv
import aiohttp
from starlette.responses import Response
from typing import Optional
from fastapi import Depends
from config import tracker
from helper import create_or_update_table
import pymysql
from contextlib import closing


app = FastAPI()
# client = ThetaClient(launch=False)
# # You might need to let the code sleep for 2 seconds to allow the API to connect to thet Theta Terminal.
# time.sleep(2)


@app.get("/")
async def root():
    return {"message": "Accessing Analytics Backend Server"}


@app.get("/fetch_data")
async def fetch_data(
    root: str,
    exp: str,
    start_date: str,
    end_date: str,
    right: str,
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
    if right in ['P', 'C']:
        url = f"http://127.0.0.1:25510/v2/bulk_hist/option/open_interest?root={root}&exp={exp}&start_date={start_date}&end_date={end_date}&use_csv=true"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                table_name = f'{root}_{exp}'
                if response.status == 200:
                    create_or_update_table(table_name, conn)
                    if response.content_type == "application/json":
                        data = await response.json()
                        if right == 'P':
                            data['response'] = [i for i in data['response'] if i['contract']['right'] == 'P']
                        elif right == 'C':
                            data['response'] = [i for i in data['response'] if i['contract']['right'] == 'C']
                        for i in data['response']:
                            print(i)
                        return data
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
                                sql = f"""DELETE from {table_name}"""
                                cur.execute(sql)
                                connection.commit()
                                for row in csv_rows:
                                    print(row)
                                    ticker, expiration, strike, call_put, ms_of_day, open_interest, date = row
                                    sql = f"""INSERT INTO {table_name} 
                                             (ticker, expiration_date, strike, call_put, ms_of_day, open_interest, date) 
                                             VALUES (%s, %s, %s, %s, %s, %s, %s)"""
                                    values = (ticker, expiration, strike, call_put, ms_of_day, int(open_interest), date)

                                    try:
                                        cur.execute(sql, values)
                                    except pymysql.Error as e:
                                        import traceback
                                        print(traceback.format_exc())
                                        print(f"Error: {e}")

                                connection.commit()

                            print(f"{type(csv_data)}")
                            return Response(content=csv_data, headers=headers)
                        except Exception as err:
                            import traceback
                            print(traceback.format_exc())
                            pass
                else:
                    print(response)
                    return {"error": f"Unexpected response: {response.status} ({response.reason})"}
    else:
        return {"error": "Invalid 'right' parameter. Must be 'P' or 'C'."}
# fetch_data('SPWX', '20231103', '20231103', '20240511')