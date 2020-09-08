# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

from odoo.exceptions import UserError
from datetime import datetime
from dateutil.relativedelta import relativedelta

class SalesSubscription(models.Model):
    _inherit = 'sale.subscription'


    coupon_program = fields.Many2one('sale.coupon.program','Coupon Program')
    apper_generate_coupon = fields.Boolean(default=False)

    end_date = fields.Date('End Date',required = True)
    freez_duration = fields.Integer('Freezing Duration')
    new_end_date = fields.Date()
    last_state = fields.Integer()
    un_freez_date = fields.Date()
    is_freez = fields.Boolean(default=False)

    freeze_times = fields.Integer(compute='_get_freeze_times')
    display_name = fields.Char(related='stage_id.display_name')


    def acrion_unfreeze(self):
        print ('unfreez')
        today = fields.Date.from_string(fields.Date.today())

        date_1 = datetime.strptime(str(today), '%Y-%m-%d')
        date_2 =  datetime.strptime(str(self.un_freez_date), '%Y-%m-%d')
        delta = date_2 - date_1
        self.template_id.new_freeze_for = int(delta.days)
        self.is_freez = False
        self.freez_duration = self.freez_duration +1

        search = self.env['sale.subscription.stage'].search

        stage = search([('in_progress', '=', False)], limit=1)
        self.stage_id = stage.id



    def action_freez(self):
        print('Freezing')

        freeze_for = 0
        if self.template_id.new_freeze_for > 0 :
            freeze_for = self.template_id.new_freeze_for
        else:
            freeze_for = self.template_id.freeze_for

        if freeze_for == 0 :
            raise UserError('Please Enter Freezing Duration First')
        if freeze_for < 0 :
            raise UserError('Wrong Vlaue for Freezing Duration')

        self.last_state = self.stage_id.id
        self.new_end_date = datetime.strptime(str(self.end_date), '%Y-%m-%d')+relativedelta(days =+ freeze_for)
        today = fields.Date.from_string(fields.Date.today())
        self.un_freez_date = datetime.strptime(str(today), '%Y-%m-%d')+relativedelta(days =+ freeze_for)

        search = self.env['sale.subscription.stage'].search
        for sub in self:
            stage = search([('name', '=', 'Freezing')], limit=1)
            if not stage:
                stage = search([('in_progress', '=', False)], limit=1)
            sub.write({
                        'freez_duration' : self.freez_duration -1,
                        'is_freez': True,
                        'stage_id': stage.id, 'to_renew': False, 'date': today,
                       'last_state': self.stage_id.id ,
                       'new_end_date': datetime.strptime(str(self.end_date), '%Y-%m-%d')+relativedelta(days =+ freeze_for)  ,
                       'un_freez_date': datetime.strptime(str(today), '%Y-%m-%d')+relativedelta(days =+ freeze_for) ,
            })
            self.template_id.new_freeze_for =0

            freez_data = {
                'start_date' : today,
                'end_date' : datetime.strptime(str(today), '%Y-%m-%d')+relativedelta(days =+ freeze_for),
                'subscription_id' : self.id,
            }
            line = self.env['subscription.freeze.line'].create(freez_data)
        return True

    @api.model
    def sale_subscription_cron_fn(self):
        search = self.env['sale.subscription.stage'].search
        stage = search([('name', '=', 'Freezing')], limit=1)
        records = self.env['sale.subscription'].search([('stage_id','=',stage.id),('un_freez_date','=',fields.Date.from_string(fields.Date.today()))])
        for rec in records :
            stage = search([('in_progress', '=', False)], limit=1)
            rec.write({
                # 'stage_id' : records.last_state,
                'stage_id' : stage.id,
                'end_date' : records.new_end_date,
                'is_freez' : False,
            })

    def _get_freeze_times(self):
        operations = self.env['subscription.freeze.line'].search([('subscription_id', '=', self.id)])
        self.freeze_times = len(operations)

    def action_subscription_freeze(self):

        operations = self.env['subscription.freeze.line'].search([('subscription_id', '=', self.id)])
        list = []
        for op in operations:
            list.append(op.id)
        return {
                'name': "Freeze times",
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'tree,form',
                # 'field_parent': 'child_ids',
                'res_model': 'subscription.freeze.line',
                'target': 'current',
                'domain': [('id', 'in', list)],
            }

    @api.onchange('coupon_program')
    def _onchange_coupon_program(self):

        self.apper_generate_coupon = False
        if self.coupon_program:
            self.apper_generate_coupon = True



class SalesSubscriptionTemplate(models.Model):
    _inherit = "sale.subscription.template"

    freeze_for = fields.Integer('Freeze For')

    new_freeze_for = fields.Integer()



class SalesSubscriptionFreeze(models.Model):
    _name = "subscription.freeze.line"
    description = 'subscription Freezes'

    start_date = fields.Date("Start Date",readonly=True)
    end_date = fields.Date("End Date" ,readonly=True)

    subscription_id = fields.Many2one('sale.subscription',readonly=True)