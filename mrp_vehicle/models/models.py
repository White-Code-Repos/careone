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
        compute='get_value_from_sale')
        # , index=False, required=False, store=False
    date_deadline = fields.Datetime(
        'Deadline', compute='get_value_from_sale', index=False, required=False, store=False,
        help="Informative date allowing to define when the manufacturing order should be processed at the latest to fulfill delivery on time.")

    def get_value_from_sale(self):
        for rec in self:
            sale_order = self.env['sale.order'].search([('name', '=', rec.origin)], order='id desc', limit=1)
            rec.vehicle_id_sale = sale_order.vehicle_id
            rec.is_have_vehicle = True
            if sale_order.validity_date:
                rec.date_planned_start = sale_order.validity_date
            else:
                rec.date_planned_start = rec.create_date
            if sale_order.service_delivery:
                rec.date_deadline = sale_order.service_delivery
            else:
                rec.date_deadline = rec.create_date

    def vehicle_state_default_get(self):
        sale_order = self.env['sale.order'].search([], order='id desc', limit=1)
        if sale_order:
            return sale_order.vehicle_state
        else:
            return False


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    vehicle_state = fields.Selection(string="Vehicle State",
                                     selection=[('Good', 'Good'), ('Medium', 'Medium'), ('Bad', 'Bad'), ],
                                     required=False, )
    clarification = fields.Selection(string="Clarification", selection=[('yes', 'Yes'), ('no', 'No'), ],
                                     required=False, )
    service_delivery = fields.Datetime(string="Service Delivery", required=False, default=fields.Datetime.now)
    planned_date = fields.Datetime(string="Planned Date", compute='get_planned_date')

    @api.model
    def get_planned_date(self):
        planned_date = False
        for mrp_order in self.env['mrp.production'].search([('origin', '=', self.name),
                                                            ('state', 'in',
                                                             ['confirmed', 'planned', 'progress', 'to_close',
                                                              'done'])]):
            if mrp_order.date_planned_finished:
                planned_date = mrp_order.date_planned_finished
        self.planned_date = planned_date

    @api.onchange('service_delivery')
    def onchange_service_delivery(self):
        for i in self:
            if i.date_order and i.service_delivery:
                if i.date_order > i.service_delivery:
                    raise ValidationError(
                        "Please set Service Delivery Date properly!!!")

    def action_cancel(self):
        res = super(SaleOrder, self).action_cancel()
        for mrp_order in self.env['mrp.production'].search([('origin', '=', self.name)]):
            if mrp_order.state == 'planned' or mrp_order.date_planned_start or mrp_order.date_planned_finished:
                mrp_order.button_unplan()
            mrp_order.action_cancel()
        return res

    def show_gantt_view(self):
        action = self.env.ref('mrp.action_mrp_workorder_production').read()[0]
        action['views'] = [(self.env.ref('mrp_vehicle.mrp_workorder_view_gantt_enhanced').id, 'gantt')]
        return action
