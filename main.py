from fastapi import FastAPI, HTTPException
import csv
import aiohttp
from starlette.responses import Response
from fastapi import Depends
from config import tracker
from helper import create_or_update_table
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
    url = f"http://3.85.111.217:25510/v2/bulk_hist/option/open_interest?root={root}&exp={exp}&start_date={start_date}&end_date={end_date}&use_csv=true"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            table_name = f'{root}_{exp}'
            if response.status == 200:
                create_or_update_table(table_name, conn)
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
                            sql = f"""DELETE from {table_name}"""
                            cur.execute(sql)
                            connection.commit()
                            for row in csv_rows:
                                ticker, expiration, strike, call_put, ms_of_day, open_interest, date = row
                                sql = f"""INSERT INTO {table_name} 
                                            (ticker, expiration_date, strike, call_put, ms_of_day, open_interest, date) 
                                            VALUES (%s, %s, %s, %s, %s, %s, %s)"""
                                values = (ticker, expiration, strike, call_put, ms_of_day, int(open_interest), date)

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