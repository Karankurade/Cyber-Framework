import socket

try:
    hostname, alisase, ip= socket.gethostbyaddr("192.168.1.3")
    print(f"hostname:{hostname}")
    print(f"alisase:{alisase}")
    print(f"ip:{ip}")
    print(socket.getfqdn("192.168.1.3"))

except:
    pass


