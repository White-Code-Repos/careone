# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

from odoo.exceptions import UserError
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.tools import safe_eval
from datetime import timedelta, datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError


class SalesSubscription(models.Model):
    _inherit = 'sale.subscription'
    subs_products_ids = fields.One2many(comodel_name="subscription.product", inverse_name="subs_id", string="",
                                        required=False, )
    # coupon_program = fields.Many2one('sale.coupon.program', 'Coupon Program')
    apper_generate_coupon = fields.Boolean(default=False)

    date = fields.Date('End Date', compute="_compute_date_end")
    def _compute_date_end(self):
        for this in self:
            if this.date_start and this.template_id.recurring_rule_boundary == 'limited':
                initial_end_date = this.date_start
                freezes = this.env['subscription.freeze.line'].search([('subscription_id','=',this.id)])
                total_freeze_days = 0
                for freeze in freezes:
                    total_freeze_days = total_freeze_days + freeze.freeze_duration
                initial_end_date = initial_end_date + timedelta(days=(30*this.template_id.recurring_rule_count)) + timedelta(days=total_freeze_days)
                this.date = initial_end_date
            if not this.date:
                this.date = False


    freez_duration = fields.Integer('Freezing Duration', related='template_id.freez_duration')

    # new_end_date = fields.Date()
    last_state = fields.Integer()
    un_freez_date = fields.Date()
    is_freez = fields.Boolean(default=False)
    freeze_for = fields.Integer(string="", required=False, related='template_id.freeze_for')
    freeze_times = fields.Integer(compute='_get_freeze_times')
    display_name = fields.Char(related='stage_id.display_name')
    is_without_freeze = fields.Boolean(string="", )
    # show_freez = fields.Boolean(compute="_get_show_freez")

    # @api.onchange('subs_products_ids')
    # def set_domain(self):
    #     print("hena hena hena")
    #     return {'domain': {'subs_products_ids.vehicle_id': [('driver_id', '=', se)]}}

    @api.onchange('template_id')
    def get_products_lines(self):
        orders = self.env['sale.order'].search([('subscription_id', '=', self._origin.id), ('state', '=', 'sale')])
        shift_hours = []
        shift_duration = self.template_id.duration
        now = datetime.now() + timedelta(hours=2)
        x = self.template_id.start_hour_use
        i = 0
        records = []
        if self.subs_products_ids:
            for record in self.subs_products_ids:
                self.write({'subs_products_ids': [(2, record.id)]})
        while True:
            shift_hours.append(int(x))
            x += 1
            i += 1
            if x >= 24:
                x -= 24
            if i > shift_duration:
                break
        current_hour = int(now.strftime("%H"))
        for rec in self.template_id.subs_product_ids:
            qty = 0
            qty_per_day = 0
            # if orders:
            #     for order in orders:
            #         confirm_time = order.date_order
            #         for line in order.order_line:
            #             if rec.product_id == line.product_id and line.price_unit == 0:
            #                 qty += line.product_uom_qty
            #                 if current_hour in shift_hours:
            #                     if 0 in shift_hours and shift_hours[0] != 0:
            #                         zer_index = shift_hours.index(0)
            #                         current_hour_index = shift_hours.index(current_hour)
            #                         if zer_index > current_hour_index:
            #                             # this shift is 2 days and this is the first day
            #                             today = str((now).date()) + " " + str(shift_hours[0]) + ":00"
            #                             if datetime.strptime(today,
            #                                                  '%Y-%m-%d %H:%M') <= confirm_time <= now:
            #                                 qty_per_day += line.product_uom_qty
            #                         elif zer_index <= current_hour_index:
            #                             # second day
            #                             yesterday = str((now - timedelta(days=1)).date()) + " " + str(
            #                                 shift_hours[0]) + ":00"
            #                             if datetime.strptime(
            #                                     yesterday, '%Y-%m-%d %H:%M') <= confirm_time <= now:
            #                                 qty_per_day += line.product_uom_qty
            #                     else:
            #                         today = str((now).date()) + " " + str(shift_hours[0]) + ":00"
            #                         if datetime.strptime(today,
            #                                              '%Y-%m-%d %H:%M') <= confirm_time <= now:
            #                             qty_per_day += line.product_uom_qty
            records.append((0, 0, {
                'product_id': rec.product_id.id,
                'qty': rec.qty,
                'qty_per_day': rec.qty_per_day,
                'consumed_qty': qty,
                'qty_counter': qty_per_day,
                'subs_id': self.id
            }))
        print(records)
        self.subs_products_ids = records

    # def _get_show_freez(self):
    #     if self.end_date:
    #         today = fields.Date.from_string(fields.Date.today())
    #         date1 = datetime.strptime(str(self.end_date.strftime('%Y-%m-%d')), '%Y-%m-%d')
    #         date2 = datetime.strptime(str(today), '%Y-%m-%d')
    #         if date1 > date2:
    #             self.show_freez = True
    #         else:
    #             self.show_freez = False
    #     else:
    #         self.show_freez = False

    # def action_unfreeze(self):
    #
    #     freezing_times = self.env['subscription.freeze.line'].search([('subscription_id', '=', self.id)])
    #     duration = 0
    #     for rec in freezing_times:
    #         duration += rec.freeze_duration
    #     if self.freeze_times >= self.freeze_for or duration >= self.template_id.freez_duration:
    #         self.is_without_freeze = True
    #
    #     self.is_freez = False
    #     freez_time = self.env['subscription.freeze.line'].search([('subscription_id', '=', self.id)], limit=1,
    #                                                              order='create_date desc')
    #     x = (fields.Date.from_string(fields.Date.today()) - freez_time.start_date).days
    #     if x == 0:
    #         dur = 1
    #     else:
    #         dur = x
    #     freez_time.update({
    #         'end_date': fields.Date.from_string(fields.Date.today()),
    #         'freeze_duration': dur
    #     })

    # def action_freez(self):
    #     print(self.freeze_for)
    #     print(self.freeze_times)
    #     freeze_for = self.template_id.freeze_for
    #     if freeze_for == 0:
    #         raise UserError('Please Enter Freezing Duration First')
    #     if freeze_for < 0:
    #         raise UserError('Wrong Value for Freezing Duration')
    #     self.last_state = self.stage_id.id
    #     today = fields.Date.from_string(fields.Date.today())
    #     self.write({
    #         'is_freez': True,
    #         'last_state': self.stage_id.id,
    #     })
    #     freez_data = {
    #         'start_date': today,
    #         'subscription_id': self.id,
    #     }
    #     self.env['subscription.freeze.line'].create(freez_data)
    #     return True

    # @api.model
    # def sale_subscription_cron_fn(self):
    #     search = self.env['sale.subscription.stage'].search
    #     stage = search([('name', '=', 'Freezing')], limit=1)
    #     records = self.env['sale.subscription'].search(
    #         [('stage_id', '=', stage.id), ('un_freez_date', '=', fields.Date.from_string(fields.Date.today()))])
    #     for rec in records:
    #         stage = search([('in_progress', '=', True)], limit=1)
    #         rec.write({
    #             'stage_id': stage.id,
    #             'end_date': records.new_end_date,
    #             'is_freez': False,
    #         })

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
            'context': {'default_subscription_id':self.id}
        }


class SalesSubscriptionTemplate(models.Model):
    _inherit = "sale.subscription.template"
    freeze_for = fields.Integer('Freeze For')
    start_hour_use = fields.Float(string="Start Hour", required=False, )
    duration = fields.Float(string="Shift Hours", required=False, )
    end_hour_use = fields.Float(string="To", required=False, )
    new_freeze_for = fields.Integer()
    # end_date = fields.Date('End Date',required = True)
    freez_duration = fields.Integer('Freezing Duration')
    subs_product_ids = fields.One2many(comodel_name="subscription.product.template", inverse_name="template_id",
                                       string="",
                                       required=False, )

    @api.onchange('start_hour_use', 'duration')
    def _onchange_start_hour_use(self):
        x = self.start_hour_use + self.duration
        self.end_hour_use = x
        if x >= 24:
            for rec in range(7):
                x -= 24
                if x < 0:
                    x += 24
                    break
            self.end_hour_use = x


class SubscriptionProductsTemplate(models.Model):
    _name = 'subscription.product.template'
    template_id = fields.Many2one(comodel_name="sale.subscription.template", string="", required=False, )
    product_id = fields.Many2one(comodel_name="product.product", string="Product", required=False,
                                 domain="[('recurring_invoice','=',False)]")
    qty = fields.Integer(string="Quantity", required=False, )
    qty_per_day = fields.Integer(string="Quantity Per Day", required=False, )


class SubscriptionProducts(models.Model):
    _name = 'subscription.product'

    subs_id = fields.Many2one(comodel_name="sale.subscription", string="", required=False, )
    product_id = fields.Many2one(comodel_name="product.product", string="Product", required=False, )
    qty = fields.Integer(string="Quantity", required=False, )
    qty_per_day = fields.Integer(string="Quantity Per Day", required=False, )
    consumed_qty = fields.Integer(string="Consumed Qty", required=False, )
    qty_counter = fields.Integer(string="Consumed Qty Per Day", required=False)
    partner_id = fields.Many2one(comodel_name="res.partner", string="", required=False,related='subs_id.partner_id' )
    vehicle_id = fields.Many2one('fleet.vehicle', 'Vehicle', help='Vehicle concerned by this log',
                                 domain="[('driver_id', '=', partner_id)]")

class SalesSubscriptionFreeze(models.Model):
    _name = "subscription.freeze.line"
    description = 'subscription Freezes'
    start_date = fields.Date("Start Date", readonly=False)
    end_date = fields.Date("End Date", readonly=False)
    freeze_duration = fields.Integer(string="Duration", required=False, )
    subscription_id = fields.Many2one('sale.subscription', readonly=False)

    @api.onchange('start_date','end_date')
    def calc_freeze_duration(self):
        if self.start_date and self.end_date:
            self.freeze_duration = (self.end_date - self.start_date).days + 1
    @api.model
    def create(self, values):
        subscription_id = self.env['sale.subscription'].browse(values['subscription_id'])
        start_date = values['start_date']
        end_date = values['end_date']
        freeze_duration = values['freeze_duration']
        freeze_duration_limit = subscription_id.template_id.freez_duration
        freeze_times_limit = subscription_id.template_id.freeze_for
        old_freezes = self.env['subscription.freeze.line'].search([('subscription_id','=',subscription_id.id)])
        if len(old_freezes) >= freeze_times_limit:
            raise ValidationError("This subscription reached freezing times limit")
        current_freezed_duration = 0
        for freeze in old_freezes:
            current_freezed_duration = current_freezed_duration + freeze.freeze_duration
        current_freezed_duration = current_freezed_duration + freeze_duration
        if current_freezed_duration > freeze_duration_limit:
            raise ValidationError("This subscription reached freezing duration limit")
        res = super(SalesSubscriptionFreeze, self).create(values)
        # if res:
        #     res.subscription_id
        return res

    def write(self, values):
        res = super(SalesSubscriptionFreeze, self).write(values)
        subscription_id = self.env['sale.subscription'].browse(self.subscription_id.id)
        start_date = self.start_date
        end_date = self.end_date
        freeze_duration = self.freeze_duration
        freeze_duration_limit = subscription_id.template_id.freez_duration
        freeze_times_limit = subscription_id.template_id.freeze_for
        old_freezes = self.env['subscription.freeze.line'].search([('subscription_id','=',subscription_id.id)])
        if len(old_freezes) > freeze_times_limit:
            raise ValidationError("This subscription reached freezing times limit")
        current_freezed_duration = 0
        for freeze in old_freezes:
            if not freeze == self:
                current_freezed_duration = current_freezed_duration + freeze.freeze_duration
        current_freezed_duration = current_freezed_duration + freeze_duration
        if current_freezed_duration > freeze_duration_limit:
            raise ValidationError("This subscription reached freezing duration limit")
        return res

    # def get_freeze_duration(self):
    #     for record in self:
    #         x = 0
    #         if record.start_date and record.end_date:
    #             x = (record.end_date - record.end_date).days
    #             if x == 0:
    #                 self.freeze_duration = 1
    #             else:
    #                 self.freeze_duration = x
    #         self.freeze_duration = x
    #


class SalesOrderInherit(models.Model):
    _inherit = 'sale.order'

    @api.onchange('partner_id')
    def _compute_subscriper_state(self):
        if self.partner_id:
            if self.partner_id.subscription_count > 0:
                subscriptions = self.env['sale.subscription'].search([('partner_id','=',self.partner_id.id)])
                for sub in subscriptions:
                    if sub.in_progress:
                        return {
                        'type': 'ir.actions.client',
                        'tag': 'action_warn',
                        'name': 'Notice',
                        'params': {'title': 'Notice','text': 'This is already a subscriper.','sticky': True}
                        }
                        # msg = "This is already a subscriper"
                        # raise UserError(_(msg))

    @api.onchange('subscription_id')
    def check_freeze(self):
        if self.subscription_id:
            freeze_line = self.env['subscription.freeze.line'].search([('subscription_id','=',self.subscription_id.id)])
            now = datetime.now().date()
            already_freezed = False
            total_freeze_days = 0
            for line in freeze_line:
                total_freeze_days = total_freeze_days + line.freeze_duration
                if line.start_date <= now <= line.end_date:
                    already_freezed = True
            if already_freezed:
                raise ValidationError("This subscription is already frozen")
            if self.subscription_id.template_id.recurring_rule_boundary == 'limited':
                sub_end_data = self.subscription_id.date_start + timedelta(days=30*self.subscription_id.template_id.recurring_rule_count) + timedelta(days=total_freeze_days)
                if sub_end_data < now:
                    raise ValidationError("This subscription is already Expired")







    subscription_id = fields.Many2one(comodel_name="sale.subscription", string="Subscription", required=False,
                                      domain="[('partner_id', '=', partner_id),('stage_id.in_progress','=',True)]", )

    def _prepare_subscription_data(self, template, no_of_vehicles):
        """Prepare a dictionnary of values to create a subscription from a template."""
        self.ensure_one()
        date_today = fields.Date.context_today(self)
        recurring_invoice_day = date_today.day
        recurring_next_date = self.env['sale.subscription']._get_recurring_next_date(
            template.recurring_rule_type, template.recurring_interval,
            date_today, recurring_invoice_day
        )
        records = []
        for rec in template.subs_product_ids:
            for record in range(no_of_vehicles):
                records.append((0, 0, {
                    'vehicle_id': self.vehicle_id.id,
                    'product_id': rec.product_id.id,
                    'qty': rec.qty,
                    'qty_per_day': rec.qty_per_day,
                    'consumed_qty': 0,
                    'qty_counter': 0,
                }))
        values = {
            'name': template.name,
            'template_id': template.id,
            'partner_id': self.partner_invoice_id.id,
            'user_id': self.user_id.id,
            'team_id': self.team_id.id,
            'date_start': fields.Date.today(),
            'description': self.note or template.description,
            'pricelist_id': self.pricelist_id.id,
            'company_id': self.company_id.id,
            'analytic_account_id': self.analytic_account_id.id,
            'recurring_next_date': recurring_next_date,
            'recurring_invoice_day': recurring_invoice_day,
            'payment_token_id': self.transaction_ids.get_last_transaction().payment_token_id.id if template.payment_mode in [
                'validate_send_payment', 'success_payment'] else False,
            'subs_products_ids': records
        }
        default_stage = self.env['sale.subscription.stage'].search([('in_progress', '=', True)], limit=1)
        if default_stage:
            values['stage_id'] = default_stage.id
        return values

    def create_subscriptions(self):
        res = []
        for order in self:
            to_create = self._split_subscription_lines()
            # create a subscription for each template with all the necessary lines
            for template in to_create:
                products = []
                no_of_vehicles = 0
                for rec in order.order_line:
                    products.append(rec.product_id)
                for rec in products:
                    if rec.subscription_template_id == template:
                        no_of_vehicles = rec.no_of_vehicles
                values = order._prepare_subscription_data(template, no_of_vehicles)
                values['recurring_invoice_line_ids'] = to_create[template]._prepare_subscription_line_data()
                values['stage_id'] = self.env['sale.subscription.stage'].search([('name','=','In Progress'),('in_progress','=',True)]).id
                subscription = self.env['sale.subscription'].sudo().create(values)
                subscription.onchange_date_start()
                res.append(subscription.id)
                to_create[template].write({'subscription_id': subscription.id})
                subscription.message_post_with_view(
                    'mail.message_origin_link', values={'self': subscription, 'origin': order},
                    subtype_id=self.env.ref('mail.mt_note').id, author_id=self.env.user.partner_id.id
                )
        return res

    # @api.onchange('subscription_id')
    # def onchange_method(self):
    #     if self.subscription_id:
    #         print(self.id)
    #         records = []
    #         sub = self.env['sale.subscription'].search([('id', '=', self.subscription_id.id)])
    #         if self.order_line:
    #             for record in self.order_line:
    #                 if record.price_unit == 0:
    #                     self.write({'order_line': [(2, record.id)]})
    #         for rec in sub.subs_products_ids:
    #             if not self.customer_vehicle_id:
    #                 self.order_line |= self.env['sale.order.line'].new({
    #                     'product_id': rec.product_id.id,
    #                     'name': self.env['sale.order.line'].get_sale_order_line_multiline_description_sale(
    #                         rec.product_id),
    #                     'product_uom_qty': rec.qty_per_day,
    #                     'price_unit': 0,
    #                     'display_type': self.env['sale.order.line'].default_get(['display_type'])['display_type'],
    #                     'product_uom': rec.product_id.uom_id.id,
    #                 })
    #             elif rec.vehicle_id == self.customer_vehicle_id:
    #                 self.order_line |= self.env['sale.order.line'].new({
    #                     'product_id': rec.product_id.id,
    #                     'name': self.env['sale.order.line'].get_sale_order_line_multiline_description_sale(
    #                         rec.product_id),
    #                     'product_uom_qty': rec.qty_per_day,
    #                     'price_unit': 0,
    #                     'display_type': self.env['sale.order.line'].default_get(['display_type'])['display_type'],
    #                     'product_uom': rec.product_id.uom_id.id,
    #                 })
    @api.onchange('order_line')
    def change_price_cancel(self):
        if self.subscription_id:
            for line in self.order_line:
                line.price_unit = 0
    def action_confirm(self):
        orders = self.env['sale.order'].search(
            [('subscription_id', '=', self.subscription_id.id), ('state', '=', 'sale')])
        shift_hours = []
        shift_duration = self.subscription_id.template_id.duration
        now = datetime.now() + timedelta(hours=2)
        x = self.subscription_id.template_id.start_hour_use
        i = 0
        while True:
            shift_hours.append(int(x))
            x += 1
            i += 1
            if x >= 24:
                x -= 24
            if i > shift_duration:
                break
        current_hour = int(now.strftime("%H"))
        for rec in self.subscription_id.subs_products_ids:
            # rec.qty_counter = 0
            for order in orders:
                confirm_time = order.date_order
                for line in order.order_line:
                    if rec.product_id == line.product_id and line.price_unit == 0 and rec.vehicle_id == line.order_id.vehicle_id:
                        if current_hour in shift_hours:
                            if 0 in shift_hours and shift_hours[0] != 0:
                                zer_index = shift_hours.index(0)
                                current_hour_index = shift_hours.index(current_hour)
                                if zer_index > current_hour_index:
                                    # this shift is 2 days and this is the first day
                                    today = str((now).date()) + " " + str(shift_hours[0]) + ":00"
                                    if datetime.strptime(today,
                                                         '%Y-%m-%d %H:%M') <= confirm_time <= now:
                                        rec.qty_counter += line.product_uom_qty
                                elif zer_index <= current_hour_index:
                                    # second day
                                    yesterday = str((now - timedelta(days=1)).date()) + " " + str(
                                        shift_hours[0]) + ":00"
                                    if datetime.strptime(
                                            yesterday, '%Y-%m-%d %H:%M') <= confirm_time <= now:
                                        rec.qty_counter += line.product_uom_qty
                            else:
                                today = str((now).date()) + " " + str(shift_hours[0]) + ":00"
                                if datetime.strptime(today,
                                                     '%Y-%m-%d %H:%M') <= confirm_time <= now:
                                    rec.qty_counter += line.product_uom_qty
            # if rec.qty_counter > rec.qty_per_day:
            #     raise ValidationError(
            #         "Your Product : %s consumed quantity Mustn't Exceed the subscription Quantity for the vehicle %s per day" % (rec.product_id.display_name,rec.vehicle_id.display_name))

        for line in self.order_line:
            for rec in self.subscription_id.subs_products_ids:
                if rec.product_id == line.product_id and line.price_unit == 0 and rec.vehicle_id == line.order_id.vehicle_id:
                    if (rec.consumed_qty) > rec.qty:
                        raise ValidationError(
                            "Your Product : %s consumed quantity Mustn't Exceed the subscription Quantity for the vehicle %s" % (rec.product_id.display_name,rec.vehicle_id.display_name))
                    if (rec.qty_counter) > rec.qty_per_day:
                        raise ValidationError(
                            "Your Product : %s consumed quantity per day Mustn't Exceed the subscription Quantity for the vehicle %s per day" % (rec.product_id.display_name,rec.vehicle_id.display_name))
                    rec.consumed_qty += line.product_uom_qty
                    # rec.qty_counter += line.product_uom_qty
        return super(SalesOrderInherit, self).action_confirm()
