
def Open_port_scan(ip,arguments):

    import nmap

    nm = nmap.PortScanner()

    if arguments is None:
        arguments = ""

    nm.scan(ip,arguments=arguments)

    print(f"command line:{nm.command_line()}")

    hosts = nm.all_hosts()

    result = []

    for host in hosts:
        for proto in nm[host].all_protocols():

            print(f"protocals:{proto}")

            lport = nm[host][proto].keys()

            for port in lport:
                port_data = nm[host][proto][port]
                

                if port_data['state'] == 'open':

                    # Extract service info safely with fallback defaults
                    service_name = port_data.get('name', 'unknown')
                    product = port_data.get('product', 'unknown')
                    version = port_data.get('version', '')
                    extrainfo = port_data.get('extrainfo', '')
                    result.append({
                            'port': port,
                            'protocol': proto,
                            'status': 'open',
                            'service': service_name,
                            'extrainfo': extrainfo,
                            'version': version
                            })
    return result 







