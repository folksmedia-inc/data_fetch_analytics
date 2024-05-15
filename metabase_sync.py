import requests
import json

class Metabase():
    def __init__(self) -> None:

        self.METABASE_URL = "3.85.111.217"
        self.username = "aayush.aman@adcuratio.com"
        self.password = "Adcuratio@123"
        self.session_api_url = f"http://{self.METABASE_URL}:3000/api/session"
        self.list_of_databases_url = f"http://{self.METABASE_URL}:3000/api/database"
        self.database_name = "Options (Historical)"

    def get_session_id(self):
        payload = json.dumps({
          "username": self.username,
          "password": self.password
        })
        headers = {
          'Content-Type': 'application/json',
        }

        response = requests.request("POST", self.session_api_url, headers=headers, data=payload)
        res = response.json()
        self.session_id = res["id"]

    def get_database_id(self):
        #getting db id
        db_id = None
        headers = {
            "Content-Type": "application/json",
            "X-Metabase-Session": self.session_id
        }
        response = requests.get(self.list_of_databases_url, headers=headers)
        if response.status_code == 200:
            self.databases = response.json()
        else:
            print("Failed to retrieve database list:", response.text)

        if self.databases:
            for database in self.databases["data"]:
                if database.get("name") == self.database_name:
                    self.db_id =database.get("id")
        else:
            print("Failed to retrieve database list.")

    def sync_schema(self):

        self.get_session_id()
        
        self.get_database_id()
        
        self.sync_schema_url = f"http://{self.METABASE_URL}:3000/api/database/{self.db_id}/sync_schema"
        payload = {}
        headers = {
          'X-Metabase-Session': self.session_id,
          'Content-Typ': 'application/json',
        }

        response = requests.request("POST", self.sync_schema_url, headers=headers, data=payload)

        print(response.text)