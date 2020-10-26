# -*- coding: utf-8 -*-
# from odoo import http


# class CustomerRequirements(http.Controller):
#     @http.route('/customer_requirements/customer_requirements/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/customer_requirements/customer_requirements/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('customer_requirements.listing', {
#             'root': '/customer_requirements/customer_requirements',
#             'objects': http.request.env['customer_requirements.customer_requirements'].search([]),
#         })

#     @http.route('/customer_requirements/customer_requirements/objects/<model("customer_requirements.customer_requirements"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('customer_requirements.object', {
#             'object': obj
#         })
