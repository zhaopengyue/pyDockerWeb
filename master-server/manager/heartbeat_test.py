import random
import string
from socket import *
from tools import md5_salt
sys.path.append('..')

HOST = '192.168.1.60'
PORT = 9999

s = socket(AF_INET, SOCK_DGRAM)
s.connect(('127.0.0.1', 10000))
try:
    while True:
        message = raw_input('send message:>>')
        message = random.choice(string.ascii_letters) * random.randint(1, 10)
        encryption_message = md5_salt(message)
        s.sendall(message + '%' + encryption_message)
finally:
    s.close()