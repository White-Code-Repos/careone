from odoo import models, fields, api, _


class SubCopReport(models.TransientModel):
    _name = 'subscription.coupon.report'

    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date", required=True)
    report_type = fields.Selection(selection=[('coupon', 'Coupon'), ('subscription', 'Subscription')],
                                   string='Type', required=True)

    def print_sub_cop_report_xls(self):
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'start_date': self.start_date,
                'end_date': self.end_date,
                'type': self.report_type
            },
        }
        return self.env.ref('subscriptions_copouns_report.sub_cop_report_xlsx').report_action(self, data=data)