# -*- coding: utf-8 -*-
# from odoo import http


# class CouponProgram(http.Controller):
#     @http.route('/coupon_program/coupon_program/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/coupon_program/coupon_program/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('coupon_program.listing', {
#             'root': '/coupon_program/coupon_program',
#             'objects': http.request.env['coupon_program.coupon_program'].search([]),
#         })

#     @http.route('/coupon_program/coupon_program/objects/<model("coupon_program.coupon_program"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('coupon_program.object', {
#             'object': obj
#         })
