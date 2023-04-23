import socketserver
import http.server
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
import Pyro5.api as pyro
from dotenv import load_dotenv
load_dotenv()


HOST = "0.0.0.0"    #Running over all available ips
PORT = int(os.getenv("HOST_PORT"))#Loading from env variable
NUM_THREADS = 5 #Setting max threads



#Creating the threaded server
class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    pass


#Creating handler
class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        # Handle GET request here
        #ns = pyro.locate_ns()
        CatalogService = pyro.Proxy("PYRONAME:service.catalog")#Getting Pyro Proxy
        parsed_url = urlparse(self.path).path.split('/')
        #print(parsed_url.path.split('/'))
        #stock_name = parsed_url.path.split('/')[-1]
        if parsed_url[1] == "stocks":#Checking if correct GET request is made
            response = CatalogService.Lookup(parsed_url[-1])
            self.send_response(200)
            self.send_header('Content-Type', 'json')
            self.end_headers()
            self.wfile.write(response.encode('utf-8'))


    def do_POST(self):
        OrderService = pyro.Proxy("PYRONAME:service.order")
        parsed_url = urlparse(self.path).path.split('/')
        if parsed_url[1] == "orders":
            content_length = int(self.headers['Content-Length'])
            orderData = json.loads(self.rfile.read(content_length).decode())#Getting Post request data
            response = OrderService.Trade(orderData["name"], orderData["type"], orderData["quantity"])
            self.send_response(200)
            self.send_header('Content-Type', 'json')
            self.end_headers()
            self.wfile.write(response.encode('utf-8'))



if __name__ == "__main__":
    

    # Create thread pool
    executor = ThreadPoolExecutor(max_workers=NUM_THREADS)

    # Create threaded HTTP server
    httpd = ThreadedHTTPServer((HOST, PORT), Handler)

    # Set up handler to use thread pool
    httpd.request_queue_size = 10
    httpd.shutdown_on_request = False
    httpd.executor = executor   #Passing threaded executor to handler

    # Start server
    print("Server listening on http://{}:{}".format(HOST, PORT))
    httpd.serve_forever()
