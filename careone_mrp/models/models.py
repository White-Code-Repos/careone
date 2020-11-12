from odoo import models, fields, api
from odoo.exceptions import ValidationError


class MrpWorkcenterProductivity(models.Model):
    _inherit = "mrp.workcenter.productivity"
    @api.depends('date_end', 'date_start','loss_type','loss_type.is_calculated')
    def _compute_duration(self):
        for blocktime in self:
            if blocktime.date_end:
                d1 = fields.Datetime.from_string(blocktime.date_start)
                d2 = fields.Datetime.from_string(blocktime.date_end)
                diff = d2 - d1
                if (
                    blocktime.loss_type.calculated or (blocktime.loss_type not in ('productive', 'performance'))
                    ) and blocktime.workcenter_id.resource_calendar_id:

                    r = blocktime.workcenter_id._get_work_days_data_batch(d1, d2)[blocktime.workcenter_id.id]['hours']
                    blocktime.duration = round(r * 60, 2)
                else:
                    blocktime.duration = round(diff.total_seconds() / 60.0, 2)
            else:
                blocktime.duration = 0.0


class MrpWorkcenterProductivityLossType(models.Model):
    _inherit = "mrp.workcenter.productivity.loss.type"

    is_calculated = fields.Boolean('calculated', default=False)
    

class MrpGroup(models.Model):
    _name = 'mrp.group'
    _description= "MRP group"

    name = fields.Char(string='Name',)   
    location_id = fields.Many2one(string='location',comodel_name='stock.location', domain=[('usage','=','internal')])
    user_ids = fields.Many2many(string='Users', comodel_name='res.users', domain=[('active','in',(True,False)),('id','>',6)])

        
class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'
    mrp_group_id = fields.Many2one(string='MRP Group',comodel_name='mrp.group', related="production_id.mrp_group_id")
    user_ids = fields.Many2many(string='mrp group users',comodel_name='res.users', related="production_id.user_ids")


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    sale_order_id = fields.Many2one(comodel_name='sale.order', string='Source Sale Order')
    mrp_group_id = fields.Many2one(string='MRP Group',comodel_name='mrp.group', related="sale_order_id.mrp_group_id")
    user_ids = fields.Many2many(string='mrp group users',comodel_name='res.users',)

    @api.onchange('sale_order_id','mrp_group_id')
    @api.constrains('sale_order_id','mrp_group_id')
    def set_mrp_users(self):
        self.user_ids = self.sale_order_id.user_ids or self.mrp_group_id.user_ids

    @api.model
    def create(self, values):
        if 'origin' in values:
            # Checking first if this comes from a 'sale.order'
            sale_id = self.env['sale.order'].search([
                ('name', '=', values['origin'])
            ], limit=1)
            if sale_id:
                values['sale_order_id'] = sale_id.id
                if sale_id.client_order_ref:
                    values['origin'] = sale_id.client_order_ref
            else:
                # Checking if this production comes from a route
                production_id = self.env['mrp.production'].search([
                    ('name', '=', values['origin'])
                ])
                # If so, use the 'sale_order_id' from the parent production
                values['sale_order_id'] = production_id.sale_order_id.id

        return super(MrpProduction, self).create(values)
    

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    production_ids = fields.One2many('mrp.production', 'sale_order_id')
    production_count = fields.Integer(compute='_compute_production_count', store=True)
    mrp_group_id = fields.Many2one(string='MRP Group',comodel_name='mrp.group',)
    user_ids = fields.Many2many(string='mrp group users',comodel_name='res.users',)

    @api.onchange('mrp_group_id')
    def set_mrp_users(self):
        self.user_ids = self.mrp_group_id.user_ids

    @api.depends("production_ids")
    def _compute_production_count(self):
        for sale in self:
            sale.production_count = len(sale.production_ids)

    def action_view_production(self):
        action = self.env.ref('mrp.mrp_production_action').read()[0]
        if self.production_count > 1:
            action['domain'] = [('id', 'in', self.production_ids.ids)]
        else:
            action['views'] = [
                (self.env.ref('mrp.mrp_production_form_view').id, 'form')]
            action['res_id'] = self.production_ids.id
        return action
