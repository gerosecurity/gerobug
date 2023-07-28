from django.http import HttpResponseForbidden
import re

class ForceInternalMiddleware(object):

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        return None

    def process_exception(self, request, exception):
        return None

    def process_template_response(self, request, response):
        return response
    
    def process_request(self, request):
        allowed_hosts = ['127.0.0.1', 'localhost']
        host = request.META.get('HTTP_HOST')

        local_ip_1 = re.compile(r'10(\.([1-9]?[0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])){3}$')
        local_ip_2 = re.compile(r'172\.(1[6-9]|2[0-9]|3[0-1])(\.([1-9]?[0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])){2}$')
        local_ip_3 = re.compile(r'192\.168(\.([1-9]?[0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])){2}$')

        if local_ip_1.search(host) == None:                 # 10.0.0.0
            if local_ip_2.search(host) == None:             # 172.16.0.0
                if local_ip_3.search(host) == None:         # 192.168.0.0
                    pass
                else:
                    IP = local_ip_3.search(host)
                    allowed_hosts.append(IP)
            else:
                IP = local_ip_2.search(host)
                allowed_hosts.append(IP)
        else:
            IP = local_ip_1.search(host)
            allowed_hosts.append(IP)


        if host not in allowed_hosts:
            raise HttpResponseForbidden

        return None