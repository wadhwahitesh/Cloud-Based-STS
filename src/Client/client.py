import http.client
import time
import json
import random
import os
from dotenv import load_dotenv
load_dotenv()       #Loading .env file

HOST = "localhost"
PORT = os.getenv("HOST_PORT")
PROBAB = 0.7      #Probability for making a trade order

TRADE_TYPES = ["buy", "sell"]
STOCK_NAME = ["GameStart", "BoarCo", "MenhirCo", "FishCo"]

while True:
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

        request = json.dumps(request)
        headers = {"Content-Type": "application/json"}

        conn.request("POST", "/orders", request, headers)#Making post request
        
        response = conn.getresponse()
        print("Response:", json.loads(response.read().decode()))#Response
    conn.close()
    time.sleep(5)
