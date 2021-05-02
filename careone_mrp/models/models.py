from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError, RedirectWarning
from datetime import datetime, timedelta


class MrpGroup(models.Model):
    _name = 'mrp.group'
    _description = "MRP Group"

    name = fields.Char(string='Name', )
    location_id = fields.Many2one(string='location', comodel_name='stock.location', domain=[('usage', '=', 'internal')])
    employee_ids = fields.Many2many(string='Users', comodel_name='hr.employee',
                                    domain=[('active', 'in', (True, False)), ('id', '>', 5)])


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    production_ids = fields.One2many('mrp.production', 'sale_order_id')
    production_count = fields.Integer(compute='_compute_production_count', store=True)
    mrp_group_id = fields.Many2one(string='MRP Group', comodel_name='mrp.group', )
    employee_ids = fields.Many2many(string='mrp group users', comodel_name='hr.employee', )

    @api.onchange('mrp_group_id')
    def set_mrp_users(self):
        self.employee_ids = self.mrp_group_id.employee_ids
        con_mrp = self.env['mrp.production'].search([('origin', '=', self.name)])
        if con_mrp:
            if con_mrp.state != 'done':
                operation_type = self.env['stock.picking.type'].search(
                    [('default_location_src_id', '=', self.mrp_group_id.location_id.id),
                     ('code', '=', 'mrp_operation')], limit=1)
                last_adj_date_sql = ("update mrp_production \n"
                                     + "   set mrp_group_id ='" + str(self.mrp_group_id.id) + "' \n"
                                     + " ,picking_type_id='" + str(operation_type.id) + "' \n"
                                     + " ,location_src_id='" + str(self.mrp_group_id.location_id.id) + "' \n"

                                     + " ,location_dest_id='" + str(
                            operation_type.default_location_dest_id.id) + "' where origin ='" + str(self.name) + "';")
                max_idsql = self.env.cr.execute(last_adj_date_sql)

                last_adj_date_sql = ("update stock_move \n"
                                     + "   set location_id =" + str(
                            self.mrp_group_id.location_id.id) + " where reference ='" + str(con_mrp.name) + "'  \n"
                                     + "       and (location_dest_id = '15');")

                max_idsql = self.env.cr.execute(last_adj_date_sql)
                # max_id = self.env.cr.fetchone()

                last_adj_date_sql = ("update stock_move_line \n"
                                     + "   set location_id =" + str(
                            self.mrp_group_id.location_id.id) + " where reference='" + str(con_mrp.name) + "'  \n"
                                     + "       and (location_dest_id = '15');")

                max_idsql = self.env.cr.execute(last_adj_date_sql)
            else:
                raise UserError("Sorry You Are Trying To Edit MO that already DONE.")

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
    # group_by ='product_id'
    location_src_id = fields.Many2one(
        'stock.location', 'Components Location',
        # default=_get_default_location_src_id,
        readonly=False,
        domain="[('usage','=','internal'), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        states={'draft': [('readonly', False)]}, check_company=True,
        help="Location where the system will look for components.")
    sale_order_id = fields.Many2one(comodel_name='sale.order', string='Source Sale Order')
    mrp_group_id = fields.Many2one(string='MRP Group', comodel_name='mrp.group',
                                   readonly=False)
    employee_ids = fields.Many2many(string='mrp group users', comodel_name='hr.employee', )

    @api.onchange('sale_order_id', 'mrp_group_id')
    # @api.constrains('sale_order_id','mrp_group_id')
    def set_mrp_users(self):
        if self.sale_order_id or self.mrp_group_id:
            mrp_grp_id = self.env['mrp.group']
            self.employee_ids = self.sale_order_id.employee_ids or self.mrp_group_id.employee_ids
            if self.sale_order_id:
                mrp_grp_id = self.sale_order_id.mrp_group_id
                if self.sale_order_id.mrp_group_id:

                    self.location_src_id = mrp_grp_id.location_id
                else:
                    mrp_grp_id = self.mrp_group_id
                    self.location_src_id = self.mrp_group_id.location_id
            else:
                mrp_grp_id = self.mrp_group_id

                self.location_src_id = mrp_grp_id.location_id

            self.mrp_group_id = mrp_grp_id
            self.location_src_id = mrp_grp_id.location_id
            picktype = self.env['stock.picking.type'].search(
                [('default_location_src_id', '=', self.location_src_id.id), ('code', '=', 'mrp_operation')], limit=1)

            last_adj_date_sql = ("update stock_move \n"
                                 + "   set location_id =" + str(
                        mrp_grp_id.location_id.id) + " where reference ='" + str(self.name) + "'  \n"
                                 + "       and (location_dest_id = '15');")

            max_idsql = self.env.cr.execute(last_adj_date_sql)
            # max_id = self.env.cr.fetchone()

            last_adj_date_sql = ("update stock_move_line \n"
                                 + "   set location_id =" + str(mrp_grp_id.location_id.id) + " where reference='" + str(
                        self.name) + "'  \n"
                                 + "       and (location_dest_id = '15');")

            max_idsql = self.env.cr.execute(last_adj_date_sql)
            # max_id = self.env.cr.fetchone()

        # self.picking_type_id = self.env['stock.picking.type'].search([('default_location_src_id','=',self.location_src_id.id),('code','=','mrp_operation')],limit=1)
        # moves = self.env['stock.move.line'].search([('production_id','=',self.id),('location_dest_id','!=',self.location_dest_id.id)])
        # for move in moves:
        #     move.write({'location_id':mrp_grp_id.location_id.id})
        # moves = self.env['stock.move'].search([('production_id','=',self.id),('location_dest_id','!=',self.location_dest_id.id)])
        # for move in moves:
        #     move.write({'location_id':mrp_grp_id.location_id.id})
        # self.write({'picking_type_id':
        # self.env['stock.picking.type'].search([('default_location_src_id','=',self.location_src_id.id),('code','=','mrp_operation')],limit=1)
        # ,'location_src_id':mrp_grp_id.location_id})
        # self.location_dest_id = mrp_grp_id.location_id

    @api.model
    def create(self, values):
        if 'origin' in values:
            # Checking first if this comes from a 'sale.orde
            sale_id = self.env['sale.order'].search([
                ('name', '=', values['origin'])
            ], limit=1)
            if sale_id.mrp_group_id:
                values['sale_order_id'] = sale_id.id
                values['mrp_group_id'] = sale_id.mrp_group_id.id
                if sale_id.mrp_group_id:
                    values['location_src_id'] = sale_id.mrp_group_id.location_id.id
                    values['picking_type_id'] = self.env['stock.picking.type'].search(
                        [('default_location_src_id', '=', sale_id.mrp_group_id.location_id.id),
                         ('code', '=', 'mrp_operation')], limit=1).id
                values['employee_ids'] = sale_id.employee_ids
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

    def button_mark_done(self):
        self.ensure_one()
        self._check_company()
        for wo in self.workorder_ids:
            if wo.time_ids.filtered(lambda x: (not x.date_end) and (x.loss_type in ('productive', 'performance'))):
                raise UserError(_('Work order %s is still running') % wo.name)
        self._check_lots()

        self.post_inventory()
        # Moves without quantity done are not posted => set them as done instead of canceling. In
        # case the user edits the MO later on and sets some consumed quantity on those, we do not
        # want the move lines to be canceled.
        (self.move_raw_ids | self.move_finished_ids).filtered(lambda x: x.state not in ('done', 'cancel')).write({
            'state': 'done',
            'product_uom_qty': 0.0,
        })

        # send mail activity
        employee_id = self.env['hr.employee'].search([('user_id', '=', self.create_uid.id)])
        user_id = employee_id.user_id.id
        activity_ins = self.env['mail.activity'].sudo()
        activity_ins.create(
            {'res_id': self.id,
             'res_model_id': self.env['ir.model'].search([('model', '=', 'mrp.production')],
                                                         limit=1).id,
             'res_model': 'mrp.production',
             'activity_type_id': 3,
             'summary': 'Mrp Production is Done',
             'note': _('MO is Done'),
             'date_deadline': fields.Date.today(),
             'activity_category': 'default',
             'previous_activity_type_id': False,
             'recommended_activity_type_id': False,
             'user_id': user_id
             })
        # send mail to client
        client = self.sale_order_id.partner_id
        mail_content = "  مرحـبـا,  " + client.name + "\nلقد تم الإنتهاء من امر التصنيع رقم" + \
                       str(self.name) + "\nنشكرك لإختيارك كير وان و إعطائنا فرصة لخدمتك, و نعدك بأن نكون عند حسن ظنك , و فى حال وجود أى سؤال أو استفسار لا تتردد ابداً ف التواصل معانا عبر:" + "\n0506068020 :الجوال" + "\ninfo@care1cc.com أو الإيميل" + "\n@care1cc أو عبر موقع التواصل الاجتماعى "
        main_content = {
            'subject': _("MO Done"),
            'author_id': self.env.user.partner_id.id,
            'body_html': mail_content,
            'email_to': client.email,
        }
        print(mail_content)
        self.env['mail.mail'].sudo().create(main_content).send()
        return self.write({'date_finished': fields.Datetime.now()})


class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'
    mrp_group_id = fields.Many2one(string='MRP Group', comodel_name='mrp.group', related="production_id.mrp_group_id")
    employee_ids = fields.Many2many(string='mrp group users', comodel_name='hr.employee',
                                    related="production_id.employee_ids")

    def button_finish(self):
        self.ensure_one()
        self.end_all()
        end_date = datetime.now()
        is_lastorder = self.env['mrp.workorder'].search(
            [('state', '!=', 'done'), ('production_id', '=', self.production_id.id), ('id', '!=', self.id)])
        # if not is_lastorder:
        # self.production_id.write({'state':'to_close'})

        # self.write({'qty_producing':self.qty_production})
        # self.qty_producing = self.qty_production
        # self.production_id.post_inventory()
        # self.production_id.button_mark_done()
        # self.do_finish()

        # self.record_production()
        # workorder tree view action should redirect to the same view instead of workorder kanban view when WO mark as done.
        # if self.env.context.get('active_model') == self._name:
        #    action = self.env.ref('mrp.action_mrp_workorder_production_specific').read()[0]
        #    action['context'] = {'search_default_production_id': self.production_id.id}
        #    action['target'] = 'main'
        # else:
        # workorder tablet view action should redirect to the same tablet view with same workcenter when WO mark as done.
        #    action = self.env.ref('mrp_workorder.mrp_workorder_action_tablet').read()[0]
        #    action['context'] = {
        #        'form_view_initial_mode': 'edit',
        #        'no_breadcrumbs': True,
        #        'search_default_workcenter_id': self.workcenter_id.id
        #    }
        # action['domain'] = [('state', 'not in', ['done', 'cancel', 'pending'])]
        # return action

        # self.env['mrp.production'].search([('id','=',)])
        # self.production_id.write({'state':'to_close'})
        # sql = "update mrp_production set state='to_close' where id="+str(self.production_id.id)+" ;"
        # self.env.cr.execute(sql)

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

    @api.depends('date_end', 'date_start', 'is_calculated')
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
