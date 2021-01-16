from odoo import models, fields, api
from odoo.exceptions import ValidationError


class AccountInvoice(models.Model):
    _inherit = 'account.move'

    coupon_id = fields.Many2one(string='Coupon',comodel_name='sale.coupon.program', readonly=True)
    vehicle_id = fields.Many2one(string='Vehicle',comodel_name='fleet.vehicle', readonly=True)
    external_coupon = fields.Char(string='External Coupon', readonly=True)
    planned_date = fields.Datetime(string='planned date', readonly=True)
    
    size = fields.Selection(
        string='size',
        selection=[('small', 'small'), ('medium', 'medium'), ('large', 'Large')],
        readonly=True
    )
    vehicle_state = fields.Selection(
        string='Vehicle state',
        selection=[('Good', 'Good'), ('Medium', 'Medium'), ('Bad', 'Bad')],
        readonly=True
    )


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    analytic_account_id = fields.Many2one(string='Analytic',comodel_name='account.analytic.account',)
        
    @api.constrains('product_id')
    @api.onchange('product_id')
    def set_aa(self):
        for line in self:
            aa = self.env['account.analytic.default'].search([('product_id','=',line.product_id.id),])
            if aa:
                aa=aa[-1].analytic_id
                line.analytic_account_id = aa

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _prepare_invoice(self):
        self.ensure_one()
        vals = super(SaleOrder, self)._prepare_invoice()
        vals.update({
            'coupon_id':self.coupon_id.id,
            'vehicle_id':self.vehicle_id.id,
            'external_coupon':self.external_coupon,
            'planned_date':self.planned_date,
            'size':self.size,
            'vehicle_state':self.vehicle_state,
        })
        return vals
        