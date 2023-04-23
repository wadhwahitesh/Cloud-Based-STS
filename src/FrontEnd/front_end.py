import socketserver
import http.server
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
import Pyro5.api as pyro
from dotenv import load_dotenv
load_dotenv()


HOST = "localhost"   #Running over all available ips
PORT = int(os.getenv("HOST_PORT"))#Loading from env variable
NUM_THREADS = 5 #Setting max threads


cache = {}


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
        if parsed_url[1] == "stocks":    #Checking if correct GET request is made
            if parsed_url[-1].lower() in cache:
                print("Found in cache")
                response = cache[parsed_url[-1].lower()]
            else:
                print("Fetching...")
                response = CatalogService.Lookup(parsed_url[-1])
                cache[parsed_url[-1].lower()] = response
                print(cache)
            self.send_response(200)
            self.send_header('Content-Type', 'json')
            self.end_headers()
            self.wfile.write(response.encode('utf-8'))


    def do_POST(self):
        if self.path == '/invalidate_cache':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            stock_name = post_data.decode('utf-8').split('=')[1]
            print("Inside invalidate {}".format(stock_name))

            if stock_name.lower() in cache:
                del cache[stock_name.lower()]
            response_text = "Cache invalidated for {}".format(stock_name)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(response_text.encode('utf-8'))
        else:    
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
