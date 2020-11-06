# -*- coding: utf-8 -*-
# from odoo import http


# class SubscriptionCycle(http.Controller):
#     @http.route('/subscription_cycle/subscription_cycle/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/subscription_cycle/subscription_cycle/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('subscription_cycle.listing', {
#             'root': '/subscription_cycle/subscription_cycle',
#             'objects': http.request.env['subscription_cycle.subscription_cycle'].search([]),
#         })

#     @http.route('/subscription_cycle/subscription_cycle/objects/<model("subscription_cycle.subscription_cycle"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('subscription_cycle.object', {
#             'object': obj
#         })
