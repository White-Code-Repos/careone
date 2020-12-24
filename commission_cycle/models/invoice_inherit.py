from odoo import models, fields, api
from datetime import timedelta, datetime


class InvoiceInherit(models.Model):
    _inherit = 'account.move'

    def commission_payment_condition(self):
        invoices = self.env['account.move'].search([('is_commission_paid', '=', False)])
        for rec in invoices:
            if rec.amount_residual == 0:
                today = fields.Date.today()
                sale_order = self.env['sale.order'].search([('name', '=', rec.invoice_origin)])
                if sale_order:
                    print("ya walaaaad")
                    rec.is_commission_paid = True
                    employee = self.env['hr.employee'].search([('user_id', '=', sale_order.user_id.id)])
                    employee_team = self.env['crm.team'].search([('member_ids', '=', sale_order.user_id.id)])
                    employee_job = employee.job_id
                    employee_department = employee.department_id
                    employee_plan = False
                    team_plan = False
                    job_plan = False
                    department_plan = False
                    related_plan = False
                    if employee:
                        employee_plan = self.env['commission.plan'].search(
                            [('start_date', '<=', today), ('end_date', '>=', today),
                             ('condition', '=', 'invoice'), ('employee_ids', '=', employee.id)])
                    if employee_team:
                        team_plan = self.env['commission.plan'].search(
                            [('start_date', '<=', today), ('end_date', '>=', today),
                             ('condition', '=', 'invoice'), ('sales_team_ids', '=', employee_team.id)])
                    if employee_job:
                        job_plan = self.env['commission.plan'].search(
                            [('start_date', '<=', today), ('end_date', '>=', today),
                             ('condition', '=', 'invoice'),
                             ('job_position_ids', '=', employee_job.id)])
                    if employee_department:
                        department_plan = self.env['commission.plan'].search(
                            [('start_date', '<=', today), ('end_date', '>=', today), ('condition', '=', 'invoice'),
                             ('department_ids', '=', employee_department.id)])
                    if employee_plan:
                        related_plan = employee_plan
                    elif team_plan:
                        related_plan = team_plan
                    elif job_plan:
                        related_plan = job_plan
                    elif department_plan:
                        related_plan = department_plan
                    if related_plan:
                        for related_plan in related_plan:
                            if related_plan.condition == 'payment':
                                for order in rec.invoice_line_ids:
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
                                                new_acc = product_report_line.accomplish + order.quantity
                                                product_report_line.write({'accomplish': new_acc,'commission_date':today})
                                                for layer in product_report_line.rule_id.product_rule_info_ids:
                                                    if layer.min_qty <= product_report_line.accomplish <= layer.max_qty:
                                                        if layer.product_calculation_type == 'fixed':
                                                            
                                                            
                                                            
                                                            
                                                            product_report_line.write({'emp_comm': layer.commission,'commission_date':self.invoice_date})
                                                        else:
                                                            commission = (
                                                                                 layer.product_id.lst_price * product_report_line.accomplish) * (
                                                                                 layer.commission / 100)
                                                            product_report_line.write({'emp_comm': commission,'commission_date':self.invoice_date})
                                                        break
                                            else:
                                                commission = 0
                                                for layer in order_rule.product_rule_info_ids:
                                                    if layer.min_qty <= order.quantity <= layer.max_qty:
                                                        if layer.product_calculation_type == 'fixed':
                                                            commission = layer.commission
                                                        else:
                                                            commission = (
                                                                                 layer.product_id.lst_price * order.quantity) * (
                                                                                 layer.commission / 100)
                                                        break
                                                self.env['commission.report'].create([{'employee_id': employee.id,
                                                                                       'rule_id': order_rule.id,
                                                                                       'plan_id': related_plan.id,
                                                                                       'commission_item': str(
                                                                                           order.product_id.name),
                                                                                       'accomplish': order.quantity,
                                                                                       'emp_comm': commission,
                                                                                       'commission_date':self.invoice_date,
                                                                                       }])
                                        else:
                                            categ_report_line = self.env['commission.report'].search(
                                                [('employee_id', '=', employee.id), ('rule_id', '=', order_rule.id),
                                                 ('commission_type', '=', 'category'),
                                                 ('commission_item', '=', order.product_id.categ_id.name)])
                                            if categ_report_line:
                                                new_acc = categ_report_line.accomplish + order.price_subtotal
                                                categ_report_line.write({'accomplish': new_acc,'commission_date':today})
                                                for layer in categ_report_line.rule_id.category_rule_info_ids:
                                                    if layer.min_amount <= categ_report_line.accomplish <= layer.max_amount:
                                                        if layer.product_calculation_type == 'fixed':
                                                            categ_report_line.write({'emp_comm': layer.commission,'commission_date':self.invoice_date})
                                                        else:
                                                            new_commission = categ_report_line.accomplish * (
                                                                    layer.commission / 100)
                                                            categ_report_line.write({'emp_comm': new_commission,'commission_date':self.invoice_date})
                                                        break
                                            else:
                                                commission = 0
                                                for layer in order_rule.category_rule_info_ids:
                                                    if layer.min_amount <= order.price_subtotal:
                                                        if layer.product_calculation_type == 'fixed':
                                                            if order.price_subtotal > layer.max_amount:
                                                                commission += layer.commission
                                                            else:
                                                                if commission ==0:
                                                                    commission = layer.commission
                                                                else:
                                                                    commission = commission
                                                        else:
                                                            if order.price_subtotal> layer.max_amount:
                                                                commission += order.price_subtotal * (layer.commission / 100)
                                                            else:
                                                                if commission ==0:
                                                                    commission = order.price_subtotal * (layer.commission / 100)
                                                                else:
                                                                    commission = commission
                                                        break
                                                self.env['commission.report'].create([{'employee_id': employee.id,
                                                                                       'rule_id': order_rule.id,
                                                                                       'plan_id': related_plan.id,
                                                                                       'commission_item': str(
                                                                                           order.product_id.categ_id.name),
                                                                                       'accomplish': order.price_subtotal,
                                                                                       'emp_comm': commission,
                                                                                       'commission_date':self.invoice_date,
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
                                        new_acc = money_target_report_line.accomplish + float(rec.amount_total)
                                        money_target_report_line.write({'accomplish': new_acc})
                                        for layer in money_target_report_line.rule_id.money_rule_info_ids:
                                            if layer.min_amount <= money_target_report_line.accomplish <= layer.max_amount:
                                                if layer.product_calculation_type == 'fixed':
                                                    money_target_report_line.write({'emp_comm': layer.commission,'commission_date':self.invoice_date})
                                                else:
                                                    commission = (money_target_report_line.accomplish) * (
                                                            layer.commission / 100)
                                                    money_target_report_line.write({'emp_comm': commission,'commission_date':self.invoice_date})
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
                                            if layer.min_amount <= rec.amount_total:
                                                if layer.product_calculation_type == 'fixed':
                                                    if rec.amount_total> layer.max_amount:
                                                        commission += layer.commission
                                                    else:
                                                        if commission ==0:
                                                            commission = layer.commission
                                                        else:
                                                            commission = commission
                                                else:
                                                    if rec.amount_total > layer.max_amount:
                                                        commission += rec.amount_total * (layer.commission / 100)
                                                    else:
                                                        if commission ==0:
                                                            commission = rec.amount_total * (layer.commission / 100)
                                                        else:
                                                            commission = commission  
                                                break
                                        self.env['commission.report'].create([{'employee_id': employee.id,
                                                                               'rule_id': money_target_rule.id,
                                                                               'plan_id': related_plan.id,
                                                                               'commission_item': 'Money Target',
                                                                               'accomplish': rec.amount_total,
                                                                               'emp_comm': commission,
                                                                               'money_target_ids': records,
                                                                               'commission_date':self.invoice_date,
                                                                               }])

    is_commission_paid = fields.Boolean(string="", )

    def action_post(self):
        today = fields.Date.today()
        sale_order = self.env['sale.order'].search([('name', '=', self.invoice_origin)])
        if sale_order:
            employee = self.env['hr.employee'].search([('user_id', '=', sale_order.user_id.id)])
            employee_team = self.env['crm.team'].search([('member_ids', '=', sale_order.user_id.id)])
            employee_job = employee.job_id
            employee_department = employee.department_id
            employee_plan = False
            team_plan = False
            job_plan = False
            department_plan = False
            related_plan = False
            if employee:
                employee_plan = self.env['commission.plan'].search(
                    [('start_date', '<=', today), ('end_date', '>=', today),
                     ('condition', '=', 'invoice'), ('employee_ids', '=', employee.id)])
            if employee_team:
                team_plan = self.env['commission.plan'].search(
                    [('start_date', '<=', today), ('end_date', '>=', today),
                     ('condition', '=', 'invoice'), ('sales_team_ids', '=', employee_team.id)])
            if employee_job:
                job_plan = self.env['commission.plan'].search(
                    [('start_date', '<=', today), ('end_date', '>=', today),
                     ('condition', '=', 'invoice'),
                     ('job_position_ids', '=', employee_job.id)])
            if employee_department:
                department_plan = self.env['commission.plan'].search(
                    [('start_date', '<=', today), ('end_date', '>=', today), ('condition', '=', 'invoice'),
                     ('department_ids', '=', employee_department.id)])
            if employee_plan:
                related_plan = employee_plan
            elif team_plan:
                related_plan = team_plan
            elif job_plan:
                related_plan = job_plan
            elif department_plan:
                related_plan = department_plan
            if related_plan:
                for related_plan in related_plan:
                    if related_plan.condition == 'invoice':
                        for order in self.invoice_line_ids:
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
                                        new_acc = product_report_line.accomplish + order.quantity
                                        product_report_line.write({'accomplish': new_acc,'commission_date':today})
                                        for layer in product_report_line.rule_id.product_rule_info_ids:
                                            if layer.min_qty <= product_report_line.accomplish <= layer.max_qty:
                                                if layer.product_calculation_type == 'fixed':
                                                    product_report_line.write({'emp_comm': layer.commission,'commission_date':today})
                                                else:
                                                    commission = (
                                                                         layer.product_id.lst_price * product_report_line.accomplish) * (
                                                                         layer.commission / 100)
                                                    product_report_line.write({'emp_comm': commission,'commission_date':today})
                                                break
                                    else:
                                        commission = 0
                                        for layer in order_rule.product_rule_info_ids:
                                            if layer.min_qty <= order.quantity <= layer.max_qty:
                                                if layer.product_calculation_type == 'fixed':
                                                    commission = layer.commission
                                                else:
                                                    commission = (layer.product_id.lst_price * order.quantity) * (
                                                            layer.commission / 100)
                                                break
                                        self.env['commission.report'].create([{'employee_id': employee.id,
                                                                               'rule_id': order_rule.id,
                                                                               'plan_id': related_plan.id,
                                                                               'commission_item': str(
                                                                                   order.product_id.name),
                                                                               'accomplish': order.quantity,
                                                                               'emp_comm': commission,
                                                                               'commission_date':today,
                                                                               }])
                                else:
                                    categ_report_line = self.env['commission.report'].search(
                                        [('employee_id', '=', employee.id), ('rule_id', '=', order_rule.id),
                                         ('commission_type', '=', 'category'),
                                         ('commission_item', '=', order.product_id.categ_id.name)])
                                    if categ_report_line:
                                        new_acc = categ_report_line.accomplish + order.price_subtotal
                                        categ_report_line.write({'accomplish': new_acc,'commission_date':today})
                                        for layer in categ_report_line.rule_id.category_rule_info_ids:
                                            if layer.min_amount <= categ_report_line.accomplish <= layer.max_amount:
                                                if layer.product_calculation_type == 'fixed':
                                                    categ_report_line.write({'emp_comm': layer.commission,'commission_date':today})
                                                else:
                                                    new_commission = categ_report_line.accomplish * (
                                                            layer.commission / 100)
                                                    categ_report_line.write({'emp_comm': new_commission,'commission_date':today})
                                                break
                                    else:
                                        commission = 0
                                        for layer in order_rule.category_rule_info_ids:
                                            if layer.min_amount <= order.price_subtotal <= layer.max_amount:
                                                if layer.product_calculation_type == 'fixed':
                                                    commission = layer.commission
                                                else:
                                                    new_commission = order.price_subtotal * (layer.commission / 100)
                                                    commission = new_commission
                                                break
                                        self.env['commission.report'].create([{'employee_id': employee.id,
                                                                               'rule_id': order_rule.id,
                                                                               'plan_id': related_plan.id,
                                                                               'commission_item': str(
                                                                                   order.product_id.categ_id.name),
                                                                               'accomplish': order.price_subtotal,
                                                                               'emp_comm': commission,
                                                                               'commission_date':today
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
                                            money_target_report_line.write({'emp_comm': layer.commission,'commission_date':today})
                                        else:
                                            commission = (money_target_report_line.accomplish) * (
                                                    layer.commission / 100)
                                            money_target_report_line.write({'emp_comm': commission,'commission_date':today})
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
                                                                       'money_target_ids': records,
                                                                       'commission_date':self.invoice_date,
                                                                       }])
        return super(InvoiceInherit, self).action_post()

    def button_draft(self):
        today = fields.Date.today()
        
        sale_order = self.env['sale.order'].search([('name', '=', self.invoice_origin)])
        if sale_order:
            employee = self.env['hr.employee'].search([('user_id', '=', sale_order.user_id.id)])
            employee_team = self.env['crm.team'].search([('member_ids', '=', sale_order.user_id.id)])
            employee_job = employee.job_id
            employee_department = employee.department_id
            employee_plan = False
            team_plan = False
            job_plan = False
            department_plan = False
            related_plan = False
            if employee:
                employee_plan = self.env['commission.plan'].search(
                    [('start_date', '<=', today), ('end_date', '>=', today),
                     ('condition', '=', 'invoice'), ('employee_ids', '=', employee.id)])
            if employee_team:
                team_plan = self.env['commission.plan'].search(
                    [('start_date', '<=', today), ('end_date', '>=', today),
                     ('condition', '=', 'invoice'), ('sales_team_ids', '=', employee_team.id)])
            if employee_job:
                job_plan = self.env['commission.plan'].search(
                    [('start_date', '<=', today), ('end_date', '>=', today),
                     ('condition', '=', 'invoice'),
                     ('job_position_ids', '=', employee_job.id)])
            if employee_department:
                department_plan = self.env['commission.plan'].search(
                    [('start_date', '<=', today), ('end_date', '>=', today), ('condition', '=', 'invoice'),
                     ('department_ids', '=', employee_department.id)])
            if employee_plan:
                related_plan = employee_plan
            elif team_plan:
                related_plan = team_plan
            elif job_plan:
                related_plan = job_plan
            elif department_plan:
                related_plan = department_plan
            if related_plan:
                for related_plan in related_plan:
                    if related_plan.condition == 'invoice':
                        for order in self.invoice_line_ids:
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
                                        new_acc = product_report_line.accomplish - order.quantity
                                        product_report_line.write({'accomplish': new_acc,'commission_date':today})
                                        for layer in product_report_line.rule_id.product_rule_info_ids:
                                            if layer.min_qty <= product_report_line.accomplish <= layer.max_qty:
                                                if layer.product_calculation_type == 'fixed':
                                                    product_report_line.write({'emp_comm': layer.commission,'commission_date':today})
                                                else:
                                                    commission = (
                                                                         layer.product_id.lst_price * product_report_line.accomplish) * (
                                                                         layer.commission / 100)
                                                    product_report_line.write({'emp_comm': commission,'commission_date':today})
                                                break
                                    else:
                                        commission = 0
                                        for layer in order_rule.product_rule_info_ids:
                                            if layer.min_qty <= order.quantity <= layer.max_qty:
                                                if layer.product_calculation_type == 'fixed':
                                                    commission = layer.commission
                                                else:
                                                    commission = (layer.product_id.lst_price * order.quantity) * (
                                                            layer.commission / 100)
                                                break
                                        self.env['commission.report'].create([{'employee_id': employee.id,
                                                                               'rule_id': order_rule.id,
                                                                               'plan_id': related_plan.id,
                                                                               'commission_item': str(
                                                                                   order.product_id.name),
                                                                               'accomplish': order.quantity,
                                                                               'emp_comm': commission,
                                                                               'commission_date':today,
                                                                               }])
                                else:
                                    categ_report_line = self.env['commission.report'].search(
                                        [('employee_id', '=', employee.id), ('rule_id', '=', order_rule.id),
                                         ('commission_type', '=', 'category'),
                                         ('commission_item', '=', order.product_id.categ_id.name)])
                                    if categ_report_line:
                                        new_acc = categ_report_line.accomplish - order.price_subtotal
                                        categ_report_line.write({'accomplish': new_acc,'commission_date':today})
                                        for layer in categ_report_line.rule_id.category_rule_info_ids:
                                            if layer.min_amount <= categ_report_line.accomplish <= layer.max_amount:
                                                if layer.product_calculation_type == 'fixed':
                                                    categ_report_line.write({'emp_comm': layer.commission,'commission_date':today})
                                                else:
                                                    new_commission = categ_report_line.accomplish * (
                                                            layer.commission / 100)
                                                    categ_report_line.write({'emp_comm': new_commission,'commission_date':today})
                                                break
                                    else:
                                        commission = 0
                                        for layer in order_rule.category_rule_info_ids:
                                            if layer.min_amount <= order.price_subtotal <= layer.max_amount:
                                                if layer.product_calculation_type == 'fixed':
                                                    commission = layer.commission
                                                else:
                                                    new_commission = order.price_subtotal * (layer.commission / 100)
                                                    commission = new_commission
                                                break
                                        self.env['commission.report'].create([{'employee_id': employee.id,
                                                                               'rule_id': order_rule.id,
                                                                               'plan_id': related_plan.id,
                                                                               'commission_item': str(
                                                                                   order.product_id.categ_id.name),
                                                                               'accomplish': order.price_subtotal,
                                                                               'emp_comm': commission,
                                                                               'commission_date':today
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
                                new_acc = money_target_report_line.accomplish - float(self.amount_total)
                                money_target_report_line.write({'accomplish': new_acc})
                                for layer in money_target_report_line.rule_id.money_rule_info_ids:
                                    if layer.min_amount <= money_target_report_line.accomplish <= layer.max_amount:
                                        if layer.product_calculation_type == 'fixed':
                                            money_target_report_line.write({'emp_comm': layer.commission,'commission_date':today})
                                        else:
                                            commission = (money_target_report_line.accomplish) * (
                                                    layer.commission / 100)
                                            money_target_report_line.write({'emp_comm': commission,'commission_date':today})
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
                                                                       'money_target_ids': records,
                                                                       'commission_date':self.invoice_date,
                                                                       }])
        return super(InvoiceInherit, self).button_draft()
        
class PaymentInherit(models.Model):
    _inherit = 'account.paryment'

    def commission_payment_condition(self):
        invoices = self.env['account.move'].search([('is_commission_paid', '=', False)])
        for rec in invoices:
            if rec.amount_residual == 0:
                today = fields.Date.today()
                sale_order = self.env['sale.order'].search([('name', '=', rec.invoice_origin)])
                if sale_order:
                    print("ya walaaaad")
                    rec.is_commission_paid = True
                    employee = self.env['hr.employee'].search([('user_id', '=', sale_order.user_id.id)])
                    employee_team = self.env['crm.team'].search([('member_ids', '=', sale_order.user_id.id)])
                    employee_job = employee.job_id
                    employee_department = employee.department_id
                    employee_plan = False
                    team_plan = False
                    job_plan = False
                    department_plan = False
                    related_plan = False
                    if employee:
                        employee_plan = self.env['commission.plan'].search(
                            [('start_date', '<=', today), ('end_date', '>=', today),
                             ('condition', '=', 'invoice'), ('employee_ids', '=', employee.id)])
                    if employee_team:
                        team_plan = self.env['commission.plan'].search(
                            [('start_date', '<=', today), ('end_date', '>=', today),
                             ('condition', '=', 'invoice'), ('sales_team_ids', '=', employee_team.id)])
                    if employee_job:
                        job_plan = self.env['commission.plan'].search(
                            [('start_date', '<=', today), ('end_date', '>=', today),
                             ('condition', '=', 'invoice'),
                             ('job_position_ids', '=', employee_job.id)])
                    if employee_department:
                        department_plan = self.env['commission.plan'].search(
                            [('start_date', '<=', today), ('end_date', '>=', today), ('condition', '=', 'invoice'),
                             ('department_ids', '=', employee_department.id)])
                    if employee_plan:
                        related_plan = employee_plan
                    elif team_plan:
                        related_plan = team_plan
                    elif job_plan:
                        related_plan = job_plan
                    elif department_plan:
                        related_plan = department_plan
                    if related_plan:
                        for related_plan in related_plan:
                            if related_plan.condition == 'payment':
                                for order in rec.invoice_line_ids:
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
                                                new_acc = product_report_line.accomplish + order.quantity
                                                product_report_line.write({'accomplish': new_acc,'commission_date':today})
                                                for layer in product_report_line.rule_id.product_rule_info_ids:
                                                    if layer.min_qty <= product_report_line.accomplish <= layer.max_qty:
                                                        if layer.product_calculation_type == 'fixed':
                                                            
                                                            
                                                            
                                                            
                                                            product_report_line.write({'emp_comm': layer.commission,'commission_date':self.invoice_date})
                                                        else:
                                                            commission = (
                                                                                 layer.product_id.lst_price * product_report_line.accomplish) * (
                                                                                 layer.commission / 100)
                                                            product_report_line.write({'emp_comm': commission,'commission_date':self.invoice_date})
                                                        break
                                            else:
                                                commission = 0
                                                for layer in order_rule.product_rule_info_ids:
                                                    if layer.min_qty <= order.quantity <= layer.max_qty:
                                                        if layer.product_calculation_type == 'fixed':
                                                            commission = layer.commission
                                                        else:
                                                            commission = (
                                                                                 layer.product_id.lst_price * order.quantity) * (
                                                                                 layer.commission / 100)
                                                        break
                                                self.env['commission.report'].create([{'employee_id': employee.id,
                                                                                       'rule_id': order_rule.id,
                                                                                       'plan_id': related_plan.id,
                                                                                       'commission_item': str(
                                                                                           order.product_id.name),
                                                                                       'accomplish': order.quantity,
                                                                                       'emp_comm': commission,
                                                                                       'commission_date':self.invoice_date,
                                                                                       }])
                                        else:
                                            categ_report_line = self.env['commission.report'].search(
                                                [('employee_id', '=', employee.id), ('rule_id', '=', order_rule.id),
                                                 ('commission_type', '=', 'category'),
                                                 ('commission_item', '=', order.product_id.categ_id.name)])
                                            if categ_report_line:
                                                new_acc = categ_report_line.accomplish + order.price_subtotal
                                                categ_report_line.write({'accomplish': new_acc,'commission_date':today})
                                                for layer in categ_report_line.rule_id.category_rule_info_ids:
                                                    if layer.min_amount <= categ_report_line.accomplish <= layer.max_amount:
                                                        if layer.product_calculation_type == 'fixed':
                                                            categ_report_line.write({'emp_comm': layer.commission,'commission_date':self.invoice_date})
                                                        else:
                                                            new_commission = categ_report_line.accomplish * (
                                                                    layer.commission / 100)
                                                            categ_report_line.write({'emp_comm': new_commission,'commission_date':self.invoice_date})
                                                        break
                                            else:
                                                commission = 0
                                                for layer in order_rule.category_rule_info_ids:
                                                    if layer.min_amount <= order.price_subtotal:
                                                        if layer.product_calculation_type == 'fixed':
                                                            if order.price_subtotal > layer.max_amount:
                                                                commission += layer.commission
                                                            else:
                                                                if commission ==0:
                                                                    commission = layer.commission
                                                                else:
                                                                    commission = commission
                                                        else:
                                                            if order.price_subtotal> layer.max_amount:
                                                                commission += order.price_subtotal * (layer.commission / 100)
                                                            else:
                                                                if commission ==0:
                                                                    commission = order.price_subtotal * (layer.commission / 100)
                                                                else:
                                                                    commission = commission
                                                        break
                                                self.env['commission.report'].create([{'employee_id': employee.id,
                                                                                       'rule_id': order_rule.id,
                                                                                       'plan_id': related_plan.id,
                                                                                       'commission_item': str(
                                                                                           order.product_id.categ_id.name),
                                                                                       'accomplish': order.price_subtotal,
                                                                                       'emp_comm': commission,
                                                                                       'commission_date':self.invoice_date,
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
                                        new_acc = money_target_report_line.accomplish + float(rec.amount_total)
                                        money_target_report_line.write({'accomplish': new_acc})
                                        for layer in money_target_report_line.rule_id.money_rule_info_ids:
                                            if layer.min_amount <= money_target_report_line.accomplish <= layer.max_amount:
                                                if layer.product_calculation_type == 'fixed':
                                                    money_target_report_line.write({'emp_comm': layer.commission,'commission_date':self.invoice_date})
                                                else:
                                                    commission = (money_target_report_line.accomplish) * (
                                                            layer.commission / 100)
                                                    money_target_report_line.write({'emp_comm': commission,'commission_date':self.invoice_date})
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
                                            if layer.min_amount <= rec.amount_total:
                                                if layer.product_calculation_type == 'fixed':
                                                    if rec.amount_total> layer.max_amount:
                                                        commission += layer.commission
                                                    else:
                                                        if commission ==0:
                                                            commission = layer.commission
                                                        else:
                                                            commission = commission
                                                else:
                                                    if rec.amount_total > layer.max_amount:
                                                        commission += rec.amount_total * (layer.commission / 100)
                                                    else:
                                                        if commission ==0:
                                                            commission = rec.amount_total * (layer.commission / 100)
                                                        else:
                                                            commission = commission  
                                                break
                                        self.env['commission.report'].create([{'employee_id': employee.id,
                                                                               'rule_id': money_target_rule.id,
                                                                               'plan_id': related_plan.id,
                                                                               'commission_item': 'Money Target',
                                                                               'accomplish': rec.amount_total,
                                                                               'emp_comm': commission,
                                                                               'money_target_ids': records,
                                                                               'commission_date':self.invoice_date,
                                                                               }])

    is_commission_paid = fields.Boolean(string="", )

    def post(self):
        today = fields.Date.today()
        Invoice = self.env['acoount.move'].search([('name', '=', self.communication)])
        sale_order = self.env['sale.order'].search([('name', '=', Invoice.invoice_origin)])
        if sale_order:
            employee = self.env['hr.employee'].search([('user_id', '=', sale_order.user_id.id)])
            employee_team = self.env['crm.team'].search([('member_ids', '=', sale_order.user_id.id)])
            employee_job = employee.job_id
            employee_department = employee.department_id
            employee_plan = False
            team_plan = False
            job_plan = False
            department_plan = False
            related_plan = False
            if employee:
                employee_plan = self.env['commission.plan'].search(
                    [('start_date', '<=', today), ('end_date', '>=', today),
                     ('condition', '=', 'invoice'), ('employee_ids', '=', employee.id)])
            if employee_team:
                team_plan = self.env['commission.plan'].search(
                    [('start_date', '<=', today), ('end_date', '>=', today),
                     ('condition', '=', 'invoice'), ('sales_team_ids', '=', employee_team.id)])
            if employee_job:
                job_plan = self.env['commission.plan'].search(
                    [('start_date', '<=', today), ('end_date', '>=', today),
                     ('condition', '=', 'invoice'),
                     ('job_position_ids', '=', employee_job.id)])
            if employee_department:
                department_plan = self.env['commission.plan'].search(
                    [('start_date', '<=', today), ('end_date', '>=', today), ('condition', '=', 'invoice'),
                     ('department_ids', '=', employee_department.id)])
            if employee_plan:
                related_plan = employee_plan
            elif team_plan:
                related_plan = team_plan
            elif job_plan:
                related_plan = job_plan
            elif department_plan:
                related_plan = department_plan
            if related_plan:
                for related_plan in related_plan:
                    if related_plan.condition == 'invoice':
                        for order in Invoice.invoice_line_ids:
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
                                        new_acc = product_report_line.accomplish + order.quantity
                                        product_report_line.write({'accomplish': new_acc,'commission_date':today})
                                        for layer in product_report_line.rule_id.product_rule_info_ids:
                                            if layer.min_qty <= product_report_line.accomplish <= layer.max_qty:
                                                if layer.product_calculation_type == 'fixed':
                                                    product_report_line.write({'emp_comm': layer.commission,'commission_date':today})
                                                else:
                                                    commission = (
                                                                         layer.product_id.lst_price * product_report_line.accomplish) * (
                                                                         layer.commission / 100)
                                                    product_report_line.write({'emp_comm': commission,'commission_date':today})
                                                break
                                    else:
                                        commission = 0
                                        for layer in order_rule.product_rule_info_ids:
                                            if layer.min_qty <= order.quantity <= layer.max_qty:
                                                if layer.product_calculation_type == 'fixed':
                                                    commission = layer.commission
                                                else:
                                                    commission = (layer.product_id.lst_price * order.quantity) * (
                                                            layer.commission / 100)
                                                break
                                        self.env['commission.report'].create([{'employee_id': employee.id,
                                                                               'rule_id': order_rule.id,
                                                                               'plan_id': related_plan.id,
                                                                               'commission_item': str(
                                                                                   order.product_id.name),
                                                                               'accomplish': order.quantity,
                                                                               'emp_comm': commission,
                                                                               'commission_date':today,
                                                                               }])
                                else:
                                    categ_report_line = self.env['commission.report'].search(
                                        [('employee_id', '=', employee.id), ('rule_id', '=', order_rule.id),
                                         ('commission_type', '=', 'category'),
                                         ('commission_item', '=', order.product_id.categ_id.name)])
                                    if categ_report_line:
                                        new_acc = categ_report_line.accomplish + order.price_subtotal
                                        categ_report_line.write({'accomplish': new_acc,'commission_date':today})
                                        for layer in categ_report_line.rule_id.category_rule_info_ids:
                                            if layer.min_amount <= categ_report_line.accomplish <= layer.max_amount:
                                                if layer.product_calculation_type == 'fixed':
                                                    categ_report_line.write({'emp_comm': layer.commission,'commission_date':today})
                                                else:
                                                    new_commission = categ_report_line.accomplish * (
                                                            layer.commission / 100)
                                                    categ_report_line.write({'emp_comm': new_commission,'commission_date':today})
                                                break
                                    else:
                                        commission = 0
                                        for layer in order_rule.category_rule_info_ids:
                                            if layer.min_amount <= order.price_subtotal <= layer.max_amount:
                                                if layer.product_calculation_type == 'fixed':
                                                    commission = layer.commission
                                                else:
                                                    new_commission = order.price_subtotal * (layer.commission / 100)
                                                    commission = new_commission
                                                break
                                        self.env['commission.report'].create([{'employee_id': employee.id,
                                                                               'rule_id': order_rule.id,
                                                                               'plan_id': related_plan.id,
                                                                               'commission_item': str(
                                                                                   order.product_id.categ_id.name),
                                                                               'accomplish': order.price_subtotal,
                                                                               'emp_comm': commission,
                                                                               'commission_date':today
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
                                new_acc = money_target_report_line.accomplish + float(self.amount)
                                money_target_report_line.write({'accomplish': new_acc})
                                for layer in money_target_report_line.rule_id.money_rule_info_ids:
                                    if layer.min_amount <= money_target_report_line.accomplish <= layer.max_amount:
                                        if layer.product_calculation_type == 'fixed':
                                            money_target_report_line.write({'emp_comm': layer.commission,'commission_date':today})
                                        else:
                                            commission = (money_target_report_line.accomplish) * (
                                                    layer.commission / 100)
                                            money_target_report_line.write({'emp_comm': commission,'commission_date':today})
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
                                    if layer.min_amount <= self.amount <= layer.max_amount:
                                        if layer.product_calculation_type == 'fixed':
                                            commission = layer.commission
                                        else:
                                            commission = self.amount * (layer.commission / 100)
                                        break
                                self.env['commission.report'].create([{'employee_id': employee.id,
                                                                       'rule_id': money_target_rule.id,
                                                                       'plan_id': related_plan.id,
                                                                       'commission_item': 'Money Target',
                                                                       'accomplish': self.amount,
                                                                       'emp_comm': commission,
                                                                       'money_target_ids': records,
                                                                       'commission_date':Invoice.invoice_date,
                                                                       }])
        return super(PaymentInherit, self).post()

