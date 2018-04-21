#!coding: utf-8
""" 接收教师机发送的文件

!!! 已弃用 !!!

"""
import os
from BaseHTTPServer import BaseHTTPRequestHandler
import cgi
import docker
import threading
from etc.core_var import TMP_DIR
from etc.sys_set import IMAGE_SERVER_SLAVE_PORT


docker_client = docker.from_env()


class PostHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        print self.headers
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={
                'REQUEST_METHOD': 'POST'
            }
        )
        self.send_response(200)
        self.end_headers()
        self.wfile.write('Client: %sn ' % str(self.client_address))
        self.wfile.write('User-agent: %sn' % str(self.headers['user-agent']))
        self.wfile.write('Path: %sn' % self.path)
        self.wfile.write('Form data:n')
        for field in form.keys():
            field_item = form[field]
            filename = field_item.filename
            filevalue = field_item.value
            filesize = len(filevalue)
            print filesize
            print filename
            file_path = os.path.join(TMP_DIR, str(filename))
            with open(file_path, 'wb') as f:
                f.write(filevalue)
            os.system('docker load < ' + file_path)
        return


def start_server():
    from BaseHTTPServer import HTTPServer
    sever = HTTPServer(("", IMAGE_SERVER_SLAVE_PORT), PostHandler)
    sever.serve_forever()


def start_upload():
    thread = threading.Thread(target=start_server)
    thread.setDaemon(True)
    thread.start()

