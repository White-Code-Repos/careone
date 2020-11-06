# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class subscription_cycle(models.Model):
#     _name = 'subscription_cycle.subscription_cycle'
#     _description = 'subscription_cycle.subscription_cycle'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
