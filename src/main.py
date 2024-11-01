from http import server
import os
import requests
import sys
from json import dumps

PROMETHEUS_URL = os.environ.get("PROMETHEUS_URL", "http://localhost:9090")
PROXY_URL = os.environ.get("PROXY_URL", "localhost:9080")
KEYSTONE_URL = os.environ.get("KEYSTONE_URL", "http://192.168.122.169/identity")

def get_project_from_token(token):
    headers = {
            "X-Auth-Token": token,
            "X-Subject-Token": token
            }
    url_path = "/v3/auth/tokens"
    data = requests.get(url = KEYSTONE_URL + url_path, headers = headers, verify=False).json()

    # What's missing here is: "is this user authorized to access metrics from this project?"
    return data['token']['project']['id']


class Handler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        # receive the user request ->
        # extract the project for the request ->
        # send a request with the project to prometheus ->
        # send the data received from prometheus back to the user
        print("HEADERS RECEIVED FROM USER:", file=sys.stderr)
        print(self.headers, file=sys.stderr)

        project = get_project_from_token(self.headers['X-Auth-Token'])

        print("\nPROJECT EXTRACTED FROM TOKEN", file=sys.stderr)
        print(project, file=sys.stderr)

        headers = self.headers
        headers['X-Tenant'] = project

        print("\nHEADERS SENT TO PROMETHEUS:", file=sys.stderr)
        print(headers, file=sys.stderr)

        print("\nPROMETHEUS REQUEST", file=sys.stderr)
        print(PROMETHEUS_URL + self.path, file=sys.stderr)

        prom_resp = requests.get(url = PROMETHEUS_URL + self.path, headers = headers)

        print("\nHEADERS RECEIVED FROM PROMETHEUS", file=sys.stderr)
        print(prom_resp.headers, file=sys.stderr)

        print("\nRESPONSE CONTENT RECEIVED FROM PROMETHEUS", file=sys.stderr)
        print(prom_resp.text, file=sys.stderr)

        self.send_response(prom_resp.status_code)
        for header_key, header_value in prom_resp.headers.items():
            self.send_header(header_key, header_value)
        self.end_headers()
        self.wfile.write(prom_resp.content)

def main():
    host, port = PROXY_URL.split(":")
    httpd = server.HTTPServer((host, int(port)), Handler)
    httpd.serve_forever()

main()
