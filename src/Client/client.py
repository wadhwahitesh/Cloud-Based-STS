import http.client
import time
import json
import random
import os
from dotenv import load_dotenv
import csv
load_dotenv()       #Loading .env file

HOST = "localhost"
PORT = os.getenv("HOST_PORT")
PROBAB = 0.7      #Probability for making a trade order

TRADE_TYPES = ["buy", "sell"]
STOCK_NAME = ["GameStart", "BoarCo", "MenhirCo", "FishCo"]

FILE_NAME = "logs.csv"

with open(FILE_NAME, "w") as f:
    writer = csv.writer(f)
    writer.writerow(["Transaction ID", "Stock Name", "Order Type", "Quantity"])



for _ in range(20):
    conn = http.client.HTTPConnection(HOST, PORT)#Connecting
    stock_name = STOCK_NAME[random.randint(0, 3)]#Selecting random stock
    conn.request("GET", f"/stocks/{stock_name}")
    print(f"Query: GET {stock_name}")
    resp = conn.getresponse()
    
    print("Response:",json.loads(resp.read().decode()))#Decoding response

    if random.random()<PROBAB:#Checking for probability

        request = {
            "name": STOCK_NAME[random.randint(0, 3)],#random stock
            "quantity": random.randint(1,5),#random quantity
            "type": TRADE_TYPES[random.randint(0,1)]#random type
        }

        print(f"Query: {request['type']} {request['quantity']} {request['name']}")

        req = json.dumps(request)
        headers = {"Content-Type": "application/json"}

        conn.request("POST", "/orders", req, headers)#Making post request
        
        response = json.loads(conn.getresponse().read().decode())
        if "data" in response:
            with open(FILE_NAME, "a") as file:
                writer = csv.writer(file)
                order_details = [response["data"]["transaction_number"],
                                 request["name"], request["type"], request["quantity"]]
                writer.writerow(order_details)


        
        print("Response:", response)#Response
    conn.close()
    time.sleep(1)

transaction_ids = []
transaction_log = []
with open(FILE_NAME, "r") as f:
    reader = csv.reader(f)
    next(reader)
    for row in reader:
        transaction_ids.append(int(row[0]))
        transaction_log.append(row)
conn = http.client.HTTPConnection(HOST, PORT)
transaction_ids = ','.join(map(str, transaction_ids))
conn.request("GET", f"/logVal/{transaction_ids}")
resp = conn.getresponse()
resp = resp.read().decode()

order_transactions = list(csv.reader(resp.splitlines()))
print(resp, order_transactions)
for i, transaction in enumerate(transaction_log):
    print(transaction,order_transactions[i], transaction==order_transactions[i])

