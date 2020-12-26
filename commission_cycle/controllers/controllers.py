# -*- coding: utf-8 -*-
# from odoo import http


# class CommissionCycle(http.Controller):
#     @http.route('/commission_cycle/commission_cycle/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/commission_cycle/commission_cycle/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('commission_cycle.listing', {
#             'root': '/commission_cycle/commission_cycle',
#             'objects': http.request.env['commission_cycle.commission_cycle'].search([]),
#         })

#     @http.route('/commission_cycle/commission_cycle/objects/<model("commission_cycle.commission_cycle"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('commission_cycle.object', {
#             'object': obj
#         })
