from odoo.http import Controller, request, route

MY_IP_ROUTE = '/my/ip/'


class MyIPController(Controller):

    @route([MY_IP_ROUTE], type='http', auth="public", website=True)
    def my_ip(self, **kwargs):
        """
        Method to return the IP of the remote host that sends the request to /my/ip/

        @return: Return the IP of the remote host that sends the request to /my/ip/
        @rtype: string
        """
        return request.httprequest.environ.get('HTTP_X_REAL_IP', request.httprequest.remote_addr)
