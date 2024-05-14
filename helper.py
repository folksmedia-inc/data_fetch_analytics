
def create_or_update_table(table_name, conn):
    """
    Create a MySQL table or update its schema by adding new columns if necessary.
    
    Parameters:
    - attributes (list): A list of dictionaries, each describing a table column.
    - table_name (str): The name of the table to create or update.
    - conn (pymysql.connections.Connection): MySQL database connection object.
    """
    cur = conn[1]
    connection = conn[0]

    cur.execute(f"SHOW TABLES LIKE '{table_name}';")
    table_exists = cur.fetchone()
    print(not table_exists)

    if not table_exists:
        create_sql = f"""CREATE TABLE {table_name} (
                    `id` int NOT NULL AUTO_INCREMENT COMMENT 'Primary Key',
                    `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT 'Create Time',
                    `ticker` varchar(255) NOT NULL,
                    `expiration_date` VARCHAR(255),
                    `strike` varchar(255) NOT NULL,
                    `call_put` varchar(255) NOT NULL,
                    `ms_of_day` varchar(255) NOT NULL,
                    `open_interest` int,
                    `date` VARCHAR(255),
                    PRIMARY KEY (id)
                ) COMMENT '';"""
        print(create_sql)
        cur.execute(create_sql)
        print(f"Table {table_name} created with a default 'created_on' column.")

    else:
        print('Hey')
        pass

    # Commit changes
    connection.commit()
    connection.close()