# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

from odoo.exceptions import UserError
from datetime import datetime
from dateutil.relativedelta import relativedelta

class SalesSubscription(models.Model):
    _inherit = 'sale.subscription'

    end_date = fields.Date('End Date',required = True)
    freez_duration = fields.Integer('Freezing Duration')
    new_end_date = fields.Date()
    last_state = fields.Integer()
    un_freez_date = fields.Date()
    is_freez = fields.Boolean()

    def action_freez(self):
        print('Freezing')
        if self.freez_duration == 0 :
            raise UserError('Please Enter Freezing Duration First')
        if self.freez_duration < 0 :
            raise UserError('Wrong Vlaue for Freezing Duration')

        self.last_state = self.stage_id.id
        self.new_end_date = datetime.strptime(str(self.end_date), '%Y-%m-%d')+relativedelta(days =+ self.freez_duration)
        today = fields.Date.from_string(fields.Date.today())
        self.un_freez_date = datetime.strptime(str(today), '%Y-%m-%d')+relativedelta(days =+ self.freez_duration+1)

        search = self.env['sale.subscription.stage'].search
        for sub in self:
            stage = search([('name', '=', 'Freezing')], limit=1)
            if not stage:
                stage = search([('in_progress', '=', False)], limit=1)
            sub.write({
                        'is_freez': True,
                        'stage_id': stage.id, 'to_renew': False, 'date': today,
                       'last_state': self.stage_id.id ,
                       'new_end_date': datetime.strptime(str(self.end_date), '%Y-%m-%d')+relativedelta(days =+ self.freez_duration)  ,
                       'un_freez_date': datetime.strptime(str(today), '%Y-%m-%d')+relativedelta(days =+ self.freez_duration+ 1) ,
            })
        return True

    @api.model
    def sale_subscription_cron_fn(self):
        search = self.env['sale.subscription.stage'].search
        stage = search([('name', '=', 'Freezing')], limit=1)
        records = self.env['sale.subscription'].search([('stage_id','=',stage.id),('un_freez_date','=',fields.Date.from_string(fields.Date.today()))])
        for rec in records :
            rec.write({
                'stage_id' : records.last_state,
                'end_date' : records.new_end_date,
            })

class SalesSubscriptionTemplate(models.Model):
    _inherit = "sale.subscription.template"

    freeze_for = fields.Integer('Freeze For')