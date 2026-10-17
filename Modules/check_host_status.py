import nmap 

def nmap_scan1(ip):

    nm = nmap.PortScanner()

    nm.scan(ip, arguments= "-sn")

    return (nm.all_hosts())



