from django.core.exceptions import PermissionDenied
from django.utils.deprecation import MiddlewareMixin
import re


class ForceInternalMiddleware(MiddlewareMixin):
    def process_request(self, request):
        allowed_hosts = ['127.0.0.1', 'localhost']
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
                    allowed_hosts.append(ip_addr)
            else:
                ip_addr = str(local_ip_2.search(host).group())
                allowed_hosts.append(ip_addr)
        else:
            ip_addr = str(local_ip_1.search(host).group())
            allowed_hosts.append(ip_addr)

        if host not in allowed_hosts:
            raise PermissionDenied()

        return None