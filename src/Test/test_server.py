import pytest
import http.client
import json
import os
from dotenv import load_dotenv
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








