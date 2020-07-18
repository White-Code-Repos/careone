from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    first_visit_date = fields.Date(string='First Visit',
                                   compute='_get_customer_status')
    last_visit_date = fields.Date(string='Last Visit',
                                  compute='_get_customer_status')
    customer_status = fields.Selection([
        ('new', 'New'),
        ('continue', 'Continue'),
        ('stop_3', 'Stop 3 Months'),
        ('stop_6', 'Stop 6 Months'),
        ('stop_12', 'Stop 1 Year'),
        ('stop_over', 'Stop Over 1 Year')
    ], string='Status', compute='_get_customer_status')
    warranty_product_ids = fields.One2many(
        'warranty.product', 'partner_id', string='Warranty')
    another_address = fields.Char('Address 2')

    def _get_customer_status(self):
        sale_obj = self.env['sale.order']
        for rec in self:
            first = sale_obj.search(
                [('partner_id', '=', rec.id)],
                order='date_order asc', limit=1)

            rec.first_visit_date = first and first.date_order or False
            last = sale_obj.search(
                [('partner_id', '=', rec.id)],
                order='date_order desc', limit=1)
            rec.last_visit_date = last and last.date_order or False
            if rec.first_visit_date and rec.last_visit_date:
                months = (rec.last_visit_date.year -
                          rec.first_visit_date.year) * 12 + (
                                 rec.last_visit_date.month - rec.first_visit_date.month) + 1
                if months > 12:
                    rec.customer_status = 'stop_over'
                elif 6 < months <= 12:
                    rec.customer_status = 'stop_12'
                elif 3 < months <= 6:
                    rec.customer_status = 'stop_6'
                elif 1 < months <= 3:
                    rec.customer_status = 'stop_3'
                elif 0 < months <= 1:
                    rec.customer_status = 'continue'
                else:
                    rec.customer_status = 'new'
            else:
                rec.customer_status = 'new'


class WarranyProduct(models.Model):
    _name = 'warranty.product'
    _description = 'Warranty Product'

    partner_id = fields.Many2one('res.partner', string='Customer')
    product_id = fields.Many2one('product.product', string='Product')
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    picking_id = fields.Many2one('stock.picking', string='Delivery')
    qty = fields.Float('Quantity')
    state = fields.Selection([
        ('valid', 'Valid'),
        ('expire', 'Expired')
    ], string='State', compute='get_state')

    @api.depends('end_date')
    def get_state(self):
        for rec in self:
            rec.state = rec.end_date and rec.end_date == datetime.now().date() and 'expire' or 'valid'

    def write(self, vals):
        if vals.get('end_date') and not self.env.user.has_group(
                'base.group_system'):
            raise ValidationError(_(
                'Only Admin has rights to change end date of warranty !'))
        return super(WarranyProduct, self).write(vals)

    @api.constrains('end_date')
    def check_end_date(self):
        for rec in self:
            if rec.end_date and rec.start_date and rec.end_date < \
                    rec.start_date:
                raise ValidationError(_(
                    'End date should be greater than start date !'))


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def action_done(self):
        res = super(StockPicking, self).action_done()
        warranty_product = []
        for rec in self.filtered(lambda x: x.state == 'done'):
            for move in rec.move_lines:
                warranty_product.append({
                    'product_id': move.product_id.id,
                    'start_date': datetime.now().today(),
                    'end_date': datetime.now().today() + timedelta(
                        days=move.product_id.product_warranty),
                    'partner_id': rec.partner_id.id,
                    'picking_id': rec.id,
                    'qty': move.quantity_done,
                })
        if warranty_product:
            self.env['warranty.product'].sudo().create(warranty_product)
        return res
