from odoo import api, fields, models


class MrpWorkedProd(models.Model):
    _inherit = 'mrp.workcenter.productivity'

    def _compute_worked_hour(self):
        for rec in self:
            rec.cost_per_hour = 0.0
            if rec.user_id:
                if rec.user_id.employee_id:
                    rec.cost_per_hour = rec.user_id.employee_id.timesheet_cost

    def _compute_total_cost(self):
        for rec in self:
            rec.total_cost = 0.0
            rec.total_cost = rec.user_id.employee_id.timesheet_cost * (rec.duration/60.0)
            # print("##################################")
            # print("##################################")
            # print(rec.duration)


    cost_per_hour = fields.Monetary('Cost per hour', currency_field='currency_id', compute='_compute_worked_hour')
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', readonly=True)
    total_cost = fields.Monetary('total cost', currency_field='currency_id', compute='_compute_total_cost')


class MrpProdState(models.Model):
    _inherit = 'mrp.production'

    @api.depends('state')
    def _compute_state_grp(self):
        for rec in self:
            if rec.state == 'draft':
                rec.state_for_grp_by = 'a'
            if rec.state == 'confirmed':
                rec.state_for_grp_by = 'b'
            if rec.state == 'planned':
                rec.state_for_grp_by = 'c'
            if rec.state == 'progress':
                rec.state_for_grp_by = 'd'
            if rec.state == 'to_close':
                rec.state_for_grp_by = 'e'
            if rec.state == 'done':
                rec.state_for_grp_by = 'f'
            if rec.state == 'cancel':
                rec.state_for_grp_by = 'g'


    state_for_grp_by = fields.Selection([
        ('a','Draft'),
        ('b','Confirmed'),
        ('c','Planned') ,
        ('d','In Progress') ,
        ('e','To Close') ,
        ('f','Done') ,
        ('g','Cancelled')] ,
        string='State',
        compute='_compute_state_grp',
        readonly=True,
    )

    state_temp = fields.Selection(related='state_for_grp_by' , store=True)




    # @api.onchange('state')
    # def onchange_state_grp(self):
    #     print('###########################')
    #     print('###########################')
    #     print('###########################')
    #     print('###########################')
    #     print('###########################')
    #     if self.state == 'draft':
    #         self.state_for_grp_by = 'a'
    #     if self.state == 'confirmed':
    #         self.state_for_grp_by = 'b'
    #     if self.state == 'planned':
    #         self.state_for_grp_by = 'c'
    #     if self.state == 'progress':
    #         self.state_for_grp_by = 'd'
    #     if self.state == 'to_close':
    #         self.state_for_grp_by = 'e'
    #     if self.state == 'done':
    #         self.state_for_grp_by = 'f'
    #     if self.state == 'cancel':
    #         self.state_for_grp_by = 'g'