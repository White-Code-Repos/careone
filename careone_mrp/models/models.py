from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError, RedirectWarning
from datetime import datetime, timedelta

class MrpGroup(models.Model):
    _name = 'mrp.group'
    _description= "MRP Group"

    name = fields.Char(string='Name',)   
    location_id = fields.Many2one(string='location',comodel_name='stock.location', domain=[('usage','=','internal')])
    user_ids = fields.Many2many(string='Users', comodel_name='res.users', domain=[('active','in',(True,False)),('id','>',5)])


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


class MrpProduction(models.Model):
    _inherit = 'mrp.production'
    #group_by ='product_id'
    location_src_id = fields.Many2one(
        'stock.location', 'Components Location',
        #default=_get_default_location_src_id,
        readonly=False,
        domain="[('usage','=','internal'), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        states={'draft': [('readonly', False)]}, check_company=True,
        help="Location where the system will look for components.")
    sale_order_id = fields.Many2one(comodel_name='sale.order', string='Source Sale Order')
    mrp_group_id = fields.Many2one(string='MRP Group',comodel_name='mrp.group',
                                   readonly=False)
    user_ids = fields.Many2many(string='mrp group users',comodel_name='res.users',)


    @api.onchange('sale_order_id','mrp_group_id')
    #@api.constrains('sale_order_id','mrp_group_id')
    def set_mrp_users(self):
        self.user_ids = self.sale_order_id.user_ids or self.mrp_group_id.user_ids
        if self.sale_order_id :
            mrp_grp_id = self.sale_order_id.mrp_group_id
            if self.sale_order_id.mrp_group_id:
                
                self.location_src_id = mrp_grp_id.location_id
            else:
                self.location_src_id = self.mrp_group_id.location_id
        else:
            mrp_grp_id = self.mrp_group_id
            
            self.location_src_id = mrp_grp_id.location_id
            
        self.mrp_group_id = mrp_grp_id
        
        # self.location_dest_id = mrp_grp_id.location_id

    @api.model
    def create(self, values):
        if 'origin' in values:
            # Checking first if this comes from a 'sale.order'
            sale_id = self.env['sale.order'].search([
                ('name', '=', values['origin'])
            ], limit=1)
            if sale_id:
                values['sale_order_id'] = sale_id.id
                values['mrp_group_id']= sale_id.mrp_group_id.id
                values['user_ids']= sale_id.user_ids
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
    

class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'
    mrp_group_id = fields.Many2one(string='MRP Group',comodel_name='mrp.group', related="production_id.mrp_group_id")
    user_ids = fields.Many2many(string='mrp group users',comodel_name='res.users', related="production_id.user_ids")
    
    def button_finish(self):
        self.ensure_one()
        self.end_all()
        end_date = datetime.now()
        is_lastorder = self.env['mrp.workorder'].search([('state','!=','done'),('production_id','=',self.production_id.id),('id','!=',self.id)])
        if not is_lastorder:
            self.production_id.write({'state':'to_close'})
            #self.qty_producing = self.qty_production
            #self.production_id.post_inventory()
            #self.production_id.button_mark_done()
            
            
            #self.record_production()
            # workorder tree view action should redirect to the same view instead of workorder kanban view when WO mark as done.
            #if self.env.context.get('active_model') == self._name:
            #    action = self.env.ref('mrp.action_mrp_workorder_production_specific').read()[0]
            #    action['context'] = {'search_default_production_id': self.production_id.id}
            #    action['target'] = 'main'
            #else:
                # workorder tablet view action should redirect to the same tablet view with same workcenter when WO mark as done.
            #    action = self.env.ref('mrp_workorder.mrp_workorder_action_tablet').read()[0]
            #    action['context'] = {
            #        'form_view_initial_mode': 'edit',
            #        'no_breadcrumbs': True,
            #        'search_default_workcenter_id': self.workcenter_id.id
            #    }
            #action['domain'] = [('state', 'not in', ['done', 'cancel', 'pending'])]
            #return action
        
            #self.env['mrp.production'].search([('id','=',)])
        #self.production_id.write({'state':'to_close'})
        #sql = "update mrp_production set state='to_close' where id="+str(self.production_id.id)+" ;"
        #self.env.cr.execute(sql)
        
        return self.write({
            'state': 'done',
            'date_finished': end_date,
            'date_planned_finished': end_date
        })
    


class MrpWorkcenterProductivity(models.Model):
    _inherit = "mrp.workcenter.productivity"

    is_calculated = fields.Boolean('calculated', default=True)

    def button_pending(self):
        return self.workorder_id.button_pending()
    def button_start(self):
        return self.workorder_id.button_start()

    @api.depends('date_end', 'date_start','is_calculated')
    def _compute_duration(self):
        for blocktime in self:
            if blocktime.date_end:
                d1 = fields.Datetime.from_string(blocktime.date_start)
                d2 = fields.Datetime.from_string(blocktime.date_end)
                diff = d2 - d1
                if (blocktime.is_calculated or (blocktime.loss_type not in ('productive', 'performance'))
                    ) and blocktime.workcenter_id.resource_calendar_id:

                    r = blocktime.workcenter_id._get_work_days_data_batch(d1, d2)[blocktime.workcenter_id.id]['hours']
                    blocktime.duration = round(r * 60, 2)
                else:
                    blocktime.duration = round(diff.total_seconds() / 60.0, 2)
            else:
                blocktime.duration = 0.0
