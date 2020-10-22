# -*- coding: utf-8 -*-
# from odoo import http


# class PromotionEnhancement(http.Controller):
#     @http.route('/promotion_enhancement/promotion_enhancement/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/promotion_enhancement/promotion_enhancement/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('promotion_enhancement.listing', {
#             'root': '/promotion_enhancement/promotion_enhancement',
#             'objects': http.request.env['promotion_enhancement.promotion_enhancement'].search([]),
#         })

#     @http.route('/promotion_enhancement/promotion_enhancement/objects/<model("promotion_enhancement.promotion_enhancement"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('promotion_enhancement.object', {
#             'object': obj
#         })
