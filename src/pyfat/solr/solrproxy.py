import socketserver
from http.server import SimpleHTTPRequestHandler
import urllib.request
from dynaconf import Dynaconf

settings = Dynaconf(
    settings_files=["conf/settings.toml"],
    secrets=["conf/.secrets.toml"],
    environments=True,
    default_env="default",
    load_dotenv=True,
)

PORT = 9098

class MyProxy(SimpleHTTPRequestHandler):
    def do_GET(self):
        target_url = "http://localhost:8183" + self.path
        self._set_up_auth(target_url)

        try:
            response = urllib.request.urlopen(target_url)
            self._send_response(200, response)
        except urllib.error.URLError as e:
            self._send_response(e.code if hasattr(e, 'code') else 500, e)

    def _set_up_auth(self, url):
        passman = urllib.request.HTTPPasswordMgrWithDefaultRealm()
        passman.add_password(None, url, settings.solr_vlo_usr, settings.solr_vlo_pwd)
        authhandler = urllib.request.HTTPBasicAuthHandler(passman)
        opener = urllib.request.build_opener(authhandler)
        urllib.request.install_opener(opener)

    def _send_response(self, status_code, response):
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.end_headers()
        if hasattr(response, 'read'):
            self.copyfile(response, self.wfile)
        else:
            self.wfile.write(str(response).encode('utf-8'))

def run_server(port):
    with socketserver.ForkingTCPServer(('', port), MyProxy) as httpd:
        print(f"Now serving at port {port}")
        httpd.serve_forever()


if __name__ == '__main__':
    run_server(PORT)
