from django.core.exceptions import PermissionDenied
from django.utils.deprecation import MiddlewareMixin
from gerobug.settings import ALLOWED_HOSTS
import re, logging

class ForceInternalMiddleware(MiddlewareMixin):
    def process_request(self, request):

        print(ALLOWED_HOSTS)
        host = request.META.get('HTTP_HOST')
        host = host[0:host.find(":")]
        
        local_ip_1 = re.compile(r'10(\.([1-9]?[0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])){3}$')
        local_ip_2 = re.compile(r'172\.(1[6-9]|2[0-9]|3[0-1])(\.([1-9]?[0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])){2}$')
        local_ip_3 = re.compile(r'192\.168(\.([1-9]?[0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])){2}$')

        if local_ip_1.search(host) == None:                 # 10.0.0.0
            if local_ip_2.search(host) == None:             # 172.16.0.0
                if local_ip_3.search(host) == None:         # 192.168.0.0
                    ip_addr = None
                else:
                    ip_addr = str(local_ip_3.search(host).group())
                    ALLOWED_HOSTS.append(ip_addr)
            else:
                ip_addr = str(local_ip_2.search(host).group())
                ALLOWED_HOSTS.append(ip_addr)
        else:
            ip_addr = str(local_ip_1.search(host).group())
            ALLOWED_HOSTS.append(ip_addr)

        logging.debug("Used Host:",host)
        logging.debug("Allowed Hosts:",ALLOWED_HOSTS)
        if host not in ALLOWED_HOSTS:
            raise PermissionDenied()

        return None