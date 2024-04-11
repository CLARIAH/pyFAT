import socketserver
import http.server as SimpleHTTPServer
import urllib
import urllib.request

from dynaconf import Dynaconf

settings = Dynaconf(settings_files=["conf/settings.toml"], secrets=["conf/.secrets.toml"], environments=True, default_env="default", load_dotenv=True)

PORT = 9098
class MyProxy(SimpleHTTPServer.SimpleHTTPRequestHandler):
    def do_GET(self):
        url="http://localhost:8183"+self.path

        passman = urllib.request.HTTPPasswordMgrWithDefaultRealm()
        passman.add_password(None, url, settings.solr_vlo_usr, settings.solr_vlo_pwd)
        authhandler = urllib.request.HTTPBasicAuthHandler(passman)
        opener = urllib.request.build_opener(authhandler)
        urllib.request.install_opener(opener)
        self.headers.add_header('Content-Type', 'application/json; charset=utf-8')
        self.send_response(200)
        self.end_headers()
        self.copyfile(urllib.request.urlopen(url), self.wfile)

httpd = socketserver.ForkingTCPServer(('', PORT), MyProxy)
print ("Now serving at "+str(PORT))
httpd.serve_forever()