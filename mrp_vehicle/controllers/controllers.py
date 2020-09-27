# -*- coding: utf-8 -*-
# from odoo import http


# class MrpVehicle(http.Controller):
#     @http.route('/mrp_vehicle/mrp_vehicle/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/mrp_vehicle/mrp_vehicle/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('mrp_vehicle.listing', {
#             'root': '/mrp_vehicle/mrp_vehicle',
#             'objects': http.request.env['mrp_vehicle.mrp_vehicle'].search([]),
#         })

#     @http.route('/mrp_vehicle/mrp_vehicle/objects/<model("mrp_vehicle.mrp_vehicle"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('mrp_vehicle.object', {
#             'object': obj
#         })
