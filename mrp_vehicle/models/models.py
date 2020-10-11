from odoo import models, fields, api
from odoo.exceptions import ValidationError


class MRP_inherit(models.Model):
    _inherit = 'mrp.production'

    vehicle_id_sale = fields.Many2one('fleet.vehicle', string='Vehicle', compute='get_value_from_sale')
    is_have_vehicle = fields.Boolean(string="", compute='get_value_from_sale')
    vehicle_state = fields.Selection(string="Vehicle State",
                                     selection=[('Good', 'Good'), ('Medium', 'Medium'), ('Bad', 'Bad'), ],
                                     store=True, required=False, default=lambda self: self.vehicle_state_default_get())
    date_planned_start = fields.Datetime(
        'Planned Date', default=fields.Datetime.now,
        help="Date at which you plan to start the production.",
        compute='get_value_from_sale', index=False, required=False, store=False)

    def get_value_from_sale(self):
        for rec in self:
            sale_order = self.env['sale.order'].search([('name', '=', rec.origin)], order='id desc', limit=1)
            rec.vehicle_id_sale = sale_order.vehicle_id
            rec.is_have_vehicle = True
            if sale_order.validity_date:
                rec.date_planned_start = sale_order.validity_date
            else:
                rec.date_planned_start = rec.create_date

    def vehicle_state_default_get(self):
        sale_order = self.env['sale.order'].search([], order='id desc', limit=1)
        return sale_order.vehicle_state


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    vehicle_state = fields.Selection(string="Vehicle State",
                                     selection=[('Good', 'Good'), ('Medium', 'Medium'), ('Bad', 'Bad'), ],
                                     required=False, )
    clarification = fields.Selection(string="Clarification", selection=[('yes', 'Yes'), ('no', 'No'), ],
                                     required=False, )

    def action_cancel(self):
        for mrp_order in self.env['mrp.production'].search([('origin', '=', self.name)]):
            if mrp_order.state == 'draft':
                mrp_order.state = 'cancel'
            else:
                raise ValidationError(
                    "You Can't Cancel Sales Order That Related With Manufacturing Order with state not Draft !")
        super(SaleOrder, self).action_cancel()
