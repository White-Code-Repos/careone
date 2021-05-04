from dateutil import relativedelta

from odoo import fields, models, api, _
from datetime import datetime, timedelta


class Contract(models.Model):
    _inherit = 'hr.contract'

    # Allowances
    housing_allowance = fields.Float(string='Housing Allowance')
    mobile_allowance = fields.Float(string='Mobile Allowance')

    # Work Duration
    work_period = fields.Integer(string='Work Duration', compute='get_work_period')

    sub_contract = fields.Boolean(string='Is Sub Contract')
    contract_id = fields.Many2one(comodel_name='hr.contract',
                                  string='Main Contract', domain="[('sub_contract', '=', False)]")

    # Bank Accounts
    bank_accounts = fields.One2many(comodel_name='bank.account',
                                    inverse_name='contract_id', string="Bank Account Details")

    iban = fields.Char('IBAN')

    # Sub Contract
    sub_contract_count = fields.Integer(compute='compute_sub_contract_count')

    # Medical Insurance
    is_announcement_ins = fields.Boolean(string='Announcement Insurance')
    com_announcement_ins = fields.Float(string='Company Ann Insurance')
    emp_announcement_ins = fields.Float(string='Employee Ann Insurance')
    ann_apply_on = fields.Selection(selection=[('saudi', 'Saudi'), ('other', 'Others')], string='Apply On')
    is_pensions_ins = fields.Boolean(string='Pensions Insurance')
    com_pensions_ins = fields.Float(string='Company Pen Insurance')
    emp_pensions_ins = fields.Float(string='Employee Pen Insurance')
    pen_apply_on = fields.Selection(selection=[('saudi', 'Saudi'), ('other', 'Others')], string='Apply On')
    blank = fields.Char()  # JUst to make view more adjusted

    def _compute_detailed(self):
        for this in self:
            if this.work_period:
                date1 = datetime.strptime(str(this.date_start), '%Y-%m-%d')
                date2 = datetime.strptime(str(datetime.now()), '%Y-%m-%d %H:%M:%S.%f')
                r = relativedelta.relativedelta(date2, date1)
                this.detailed_work_duration = str(int(r.years))+" years, "+str(int(r.months))+" month, "+str(int(r.days))+" days"
            else:
                this.detailed_work_duration = "0 years, 0 month, 0 days"
    detailed_work_duration = fields.Char(compute='_compute_detailed')

    def compute_sub_contract_count(self):
        for record in self:
            record.sub_contract_count = self.env['hr.contract'].search_count([('contract_id', '=', self.id),
                                                                              ('sub_contract', '=', True)])

    def get_sub_contracts(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sub Contracts',
            'view_mode': 'tree,form',
            'res_model': 'hr.contract',
            'domain': [('contract_id', '=', self.id), ('sub_contract', '=', True)],
            'context': "{'create': False}"
        }

    @api.depends('date_start')
    def get_work_period(self):
        for item in self:
            if item.date_start:
                date1 = datetime.strptime(str(item.date_start), '%Y-%m-%d')
                date2 = datetime.strptime(str(datetime.now()), '%Y-%m-%d %H:%M:%S.%f')
                r = relativedelta.relativedelta(date2, date1)
                item.work_period = r.months + (12 * r.years)

    def mail_reminder(self):
        now = datetime.now() + timedelta(days=1)
        date_now = now.date()
        match = self.search([])
        users = self.env['res.users'].search([('groups_id', 'in', [self.env.ref('hr.group_hr_manager').id])])
        # for loop on all contracts.
        for i in match:
            if i.date_end:
                exp_date = i.date_end - timedelta(days=30)
                if date_now >= exp_date:
                    for user in users:
                        mail_content = "  Dear, Mr.  " + user.name + ",<br>The Contract (" + i.name + ") of Employee " \
                                       + i.employee_id.name + "is going to end on " + \
                                       str(i.date_end) + ". Please renew it before end date"
                        main_content = {
                            'subject': _('Contract-%s ended On %s') % (i.name, i.date_end),
                            'author_id': self.env.user.partner_id.id,
                            'body_html': mail_content,
                            'email_to': user.partner_id.email,
                        }
                        self.env['mail.mail'].create(main_content).send()
