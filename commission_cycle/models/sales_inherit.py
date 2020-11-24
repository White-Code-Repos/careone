from odoo import models, fields, api
from datetime import timedelta, datetime


class SalesOrderInherit(models.Model):
    _inherit = 'sale.order'
    is_have_permission = fields.Boolean(string="", compute='get_user_permission')

    def get_user_permission(self):
        for order in self:
            users = []
            current_login = self.env.user
            group_security_id = self.env['res.groups'].search([('category_id.name', '=', 'Sales Person Edition')],
                                                              order='id desc',
                                                              limit=1)
            for user in group_security_id.users:
                users.append(user)
            if current_login in users:
                order.is_have_permission = True
            else:
                order.is_have_permission = False

    def action_confirm(self):
        domain = []
        today = fields.Date.today()
        domain.append(('start_date', '<=', today))
        domain.append(('end_date', '>=', today))
        employee = self.env['hr.employee'].search([('user_id', '=', self.user_id.id)])
        employee_team = self.env['crm.team'].search([('member_ids', '=', self.user_id.id)])
        employee_job = employee.job_id
        employee_department = employee.department_id
        x = 0
        if employee:
            x += 1
        if employee_team:
            x += 1
        if employee_job:
            x += 1
        if employee_department:
            x += 1
        x -= 1
        if x > 0:
            for rec in range(x):
                domain.append('|')
        if employee:
            domain.append(('employee_ids', '=', employee.id))
        if employee_team:
            domain.append(('sales_team_ids', '=', employee_team.id))
        if employee_job:
            domain.append(('job_position_ids', '=', employee_job.id))
        if employee_department:
            domain.append(('department_ids', '=', employee_department.id))
        related_plan = self.env['commission.plan'].search(domain, limit=1)
        if related_plan:
            for order in self.order_line:
                current_rule = 0
                for rule in related_plan.rule_ids:
                    if rule.commission_type == 'product' and rule.product_id == order.product_id:
                        current_rule = rule.id
                        break
                    elif rule.commission_type == 'category' and rule.category_id == order.product_id.categ_id:
                        current_rule = rule.id
                order_rule = self.env['commission.rule'].search([('id', '=', current_rule)])
                if order_rule:
                    if order_rule.commission_type == 'product':
                        product_report_line = self.env['commission.report'].search(
                            [('employee_id', '=', employee.id), ('rule_id', '=', order_rule.id),
                             ('commission_type', '=', 'product'),
                             ('commission_item', '=', order.product_id.name)])
                        if product_report_line:
                            new_acc = product_report_line.accomplish + order.product_uom_qty
                            product_report_line.write({'accomplish': new_acc})
                            for layer in product_report_line.rule_id.product_rule_info_ids:
                                if layer.min_qty <= product_report_line.accomplish <= layer.max_qty:
                                    if layer.product_calculation_type == 'fixed':
                                        product_report_line.write({'emp_comm': layer.commission})
                                    else:
                                        commission = (layer.product_id.lst_price * product_report_line.accomplish) * (
                                                layer.commission / 100)
                                        product_report_line.write({'emp_comm': commission})
                                    break
                        else:
                            commission = 0
                            for layer in order_rule.product_rule_info_ids:
                                if layer.min_qty <= order.product_uom_qty <= layer.max_qty:
                                    if layer.product_calculation_type == 'fixed':
                                        commission = layer.commission
                                    else:
                                        commission = (layer.product_id.lst_price * order.product_uom_qty) * (
                                                layer.commission / 100)
                                    break
                            self.env['commission.report'].create([{'employee_id': employee.id,
                                                                   'rule_id': order_rule.id,
                                                                   'plan_id': related_plan.id,
                                                                   'commission_item': str(order.product_id.name),
                                                                   'accomplish': order.product_uom_qty,
                                                                   'emp_comm': commission,
                                                                   }])
                    else:
                        categ_report_line = self.env['commission.report'].search(
                            [('employee_id', '=', employee.id), ('rule_id', '=', order_rule.id),
                             ('commission_type', '=', 'category'),
                             ('commission_item', '=', order.product_id.categ_id.name)])
                        if categ_report_line:
                            new_acc = categ_report_line.accomplish + order.product_uom_qty
                            categ_report_line.write({'accomplish': new_acc})
                            for layer in categ_report_line.rule_id.category_rule_info_ids:
                                if layer.min_qty <= categ_report_line.accomplish <= layer.max_qty:
                                    if layer.product_calculation_type == 'fixed':
                                        categ_report_line.write({'emp_comm': layer.commission})
                                    else:
                                        new_commission = categ_report_line.emp_comm + (
                                                order.product_id.lst_price * order.product_uom_qty) * (
                                                                 layer.commission / 100)
                                        categ_report_line.write({'emp_comm': new_commission})
                                    break
                        else:
                            commission = 0
                            for layer in order_rule.category_rule_info_ids:
                                if layer.min_qty <= order.product_uom_qty <= layer.max_qty:
                                    if layer.product_calculation_type == 'fixed':
                                        commission = layer.commission
                                    else:
                                        new_commission = (order.product_id.lst_price * order.product_uom_qty) * (
                                                layer.commission / 100)
                                        commission = new_commission
                                    break
                            self.env['commission.report'].create([{'employee_id': employee.id,
                                                                   'rule_id': order_rule.id,
                                                                   'plan_id': related_plan.id,
                                                                   'commission_item': str(order.product_id.name),
                                                                   'accomplish': order.product_uom_qty,
                                                                   'emp_comm': commission,
                                                                   }])
            current_rule = 0
            for rule in related_plan.rule_ids:
                if rule.commission_type == 'money':
                    current_rule = rule.id
                    break
            money_target_rule = self.env['commission.rule'].search([('id', '=', current_rule)])
            if money_target_rule:
                money_target_report_line = self.env['commission.report'].search(
                    [('employee_id', '=', employee.id), ('rule_id', '=', money_target_rule.id)])
                if money_target_report_line:
                    new_acc = money_target_report_line.accomplish + float(self.amount_total)
                    money_target_report_line.write({'accomplish': new_acc})
                    for layer in money_target_report_line.rule_id.money_rule_info_ids:
                        if layer.min_amount <= money_target_report_line.accomplish <= layer.max_amount:
                            if layer.product_calculation_type == 'fixed':
                                money_target_report_line.write({'emp_comm': layer.commission})
                            else:
                                commission = (money_target_report_line.accomplish) * (layer.commission / 100)
                                money_target_report_line.write({'emp_comm': commission})
                            break
                else:
                    commission = 0
                    records = []
                    for layer in money_target_rule.money_rule_info_ids:
                        object = (
                            0, 0, {'calculation_type': layer.product_calculation_type,
                                   'min_amount': layer.min_amount,
                                   'max_amount': layer.max_amount,
                                   'commission': layer.commission,
                                   })
                        records.append(object)
                    for layer in money_target_rule.money_rule_info_ids:
                        if layer.min_amount <= self.amount_total <= layer.max_amount:
                            if layer.product_calculation_type == 'fixed':
                                commission = layer.commission
                            else:
                                commission = self.amount_total * (layer.commission / 100)
                            break
                    self.env['commission.report'].create([{'employee_id': employee.id,
                                                           'rule_id': money_target_rule.id,
                                                           'plan_id': related_plan.id,
                                                           'commission_item': 'Money Target',
                                                           'accomplish': self.amount_total,
                                                           'emp_comm': commission,
                                                           'money_target_ids': records
                                                           }])

        return super(SalesOrderInherit, self).action_confirm()
