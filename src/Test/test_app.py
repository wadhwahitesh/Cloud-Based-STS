import pytest
import http.client
import json
import os
from dotenv import load_dotenv
import Pyro5.api

load_dotenv()  # Loading .env file

HOST = "localhost"
PORT = 8080


def test_lookupWrongName():
    conn = http.client.HTTPConnection(HOST, port=PORT)
    conn.request("GET", f"/stocks/GameStar")

    resp = conn.getresponse()

    resp = json.loads(resp.read().decode())

    assert resp["error"]["code"] == 402
    assert resp["error"]["message"].lower() == "stock not found"#Checking for expected response

def test_orderWrongName():
    conn = http.client.HTTPConnection(HOST, port=PORT)

    request = {
        "name": "Boarc",
        "quantity": 3,
        "type": "buy"
    }

    request = json.dumps(request)
    headers = {"Content-Type": "application/json"}

    conn.request("POST", "/orders", request, headers)

    response = conn.getresponse()

    resp = json.loads(response.read().decode())

    assert resp["error"]["code"] == 402
    # Checking for expected response
    assert resp["error"]["message"].lower() == "stock not found"

def test_correctBuy():
    conn = http.client.HTTPConnection(HOST, port=PORT)
    conn.request("GET", f"/stocks/GameStart")

    resp = conn.getresponse()

    resp = json.loads(resp.read().decode())

    old_quantity = resp["quantity"]

    request = {
        "name": "gamestart",
        "quantity": 3,
        "type": "buy"
    }

    request = json.dumps(request)
    headers = {"Content-Type": "application/json"}

    conn.request("POST", "/orders", request, headers)

    response = conn.getresponse()


    conn.request("GET", f"/stocks/GameStart")

    resp = conn.getresponse()

    resp = json.loads(resp.read().decode())

    new_quantity = resp["quantity"]

    assert old_quantity == new_quantity+3#Checking if quantity of stock is correctly changed


def test_correctSell():
    conn = http.client.HTTPConnection(HOST, port=PORT)
    conn.request("GET", f"/stocks/GameStart")

    resp = conn.getresponse()

    resp = json.loads(resp.read().decode())

    old_quantity = resp["quantity"]

    request = {
        "name": "gamestart",
        "quantity": 3,
        "type": "sell"
    }

    request = json.dumps(request)
    headers = {"Content-Type": "application/json"}

    conn.request("POST", "/orders", request, headers)

    response = conn.getresponse()

    conn.request("GET", f"/stocks/GameStart")

    resp = conn.getresponse()

    resp = json.loads(resp.read().decode())

    new_quantity = resp["quantity"]

    # Checking if quantity of stock is correctly changed
    assert old_quantity == new_quantity-3


def test_buyMoreThanQuantity():
    conn = http.client.HTTPConnection(HOST, port=PORT)
    conn.request("GET", f"/stocks/GameStart")

    resp = conn.getresponse()

    resp = json.loads(resp.read().decode())

    old_quantity = resp["quantity"]

    request = {
        "name": "gamestart",
        "quantity": old_quantity+1,#Buying more than the available quantity
        "type": "buy"
    }

    request = json.dumps(request)
    headers = {"Content-Type": "application/json"}

    conn.request("POST", "/orders", request, headers)

    response = conn.getresponse()

    resp = json.loads(response.read().decode())

    assert resp["error"]["code"] == 404
    assert resp["error"]["message"].lower() == "not enough stocks"#Should get this



def test_Replication():
    conn = http.client.HTTPConnection(HOST, port=PORT)
    # Create a new order
    request = {
        "name": "gamestart",
        "quantity": 1,
        "type": "sell"
    }
    request = json.dumps(request)
    headers = {"Content-Type": "application/json"}
    conn.request("POST", "/orders", request, headers)
    response = conn.getresponse()

    # Check if the last entry in the trade logs are the same
    last_lines = []
    for i in range(1,4):
        try:
            if Pyro5.api.Proxy(f"PYRONAME:service.order{i}").healthCheck():
                with open(f"OrderService/data/tradeLog_{i}.csv") as f:
                    last_lines.append(f.readlines()[-1])
        except:
            continue

    assert len(set(last_lines)) == 1

def test_LeaderElection():
    conn = http.client.HTTPConnection(HOST, port=PORT)
    conn.request("GET", f"/leaderID")
    resp = conn.getresponse()
    resp = json.loads(resp.read().decode())
    assert resp['ID'] == 1 or resp['ID'] == 2 or resp['ID'] == 3

# def test_LeaderFailure():
#     #Get leader id
#     conn = http.client.HTTPConnection(HOST, port=PORT)
#     conn.request("GET", f"/leaderID")
#     resp = conn.getresponse()
#     resp = json.loads(resp.read().decode())
#     try:
#         Pyro5.api.Proxy(f"PYRONAME:service.order{resp['ID']}").exit_service()
#     except (Pyro5.errors.ConnectionClosedError):
#         pass
#     conn = http.client.HTTPConnection(HOST, port=PORT)
#     # Create a new order
#     request = {
#         "name": "gamestart",
#         "quantity": 1,
#         "type": "sell"
#     }
#     request = json.dumps(request)
#     headers = {"Content-Type": "application/json"}
#     conn.request("POST", "/orders", request, headers)
#     resp = conn.getresponse()
#     resp = json.loads(resp.read().decode())
#     assert resp['data']['transaction_number']!=None
    
def test_cache():
    
    conn = http.client.HTTPConnection(HOST, port=PORT)
    conn.request("GET", f"/stocks/GameStart")
    resp = conn.getresponse()

    conn.request("GET","/cache")
    resp = conn.getresponse()
    resp = json.loads(resp.read().decode())

    assert "gamestart" in resp['cache']

    request = {
        "name": "gamestart",
        "quantity": 1,
        "type": "sell"
    }
    request = json.dumps(request)
    headers = {"Content-Type": "application/json"}
    conn.request("POST", "/orders", request, headers)
    resp = conn.getresponse()


    conn.request("GET","/cache")
    resp = conn.getresponse()
    resp = json.loads(resp.read().decode())

    assert "gamestart" not in resp['cache']












