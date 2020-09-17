from odoo import models, fields, api


class MRP_inherit(models.Model):
    _inherit = 'mrp.production'

    vehicle_id_sale = fields.Many2one('fleet.vehicle', string='Vehicle', compute='get_value_from_sale')
    is_have_vehicle = fields.Boolean(string="", compute='get_value_from_sale')
    date_planned_start = fields.Datetime(
        'Planned Date', default=fields.Datetime.now,
        help="Date at which you plan to start the production.",
        compute='get_value_from_sale',index=False, required=False, store=False)

    def get_value_from_sale(self):
        for rec in self:
            sale_order = self.env['sale.order'].search([('name', '=', rec.origin)], order='id desc', limit=1)
            rec.vehicle_id_sale = sale_order.vehicle_id
            rec.is_have_vehicle = True
            if sale_order.validity_date:
                rec.write({'date_planned_start': sale_order.validity_date})
            else:
                rec.write({'date_planned_start': rec.create_date})


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    clarification = fields.Selection(string="Clarification", selection=[('yes', 'Yes'), ('no', 'No'), ],
                                     required=False, )
