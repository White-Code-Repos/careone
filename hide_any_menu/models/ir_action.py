from odoo import api, models, tools


class IrActions(models.Model):
    _inherit = 'ir.actions.actions'

    @api.model
    @tools.ormcache('frozenset(self.env.user.groups_id.ids)', 'model_name')
    def get_bindings(self, model_name):
        result = super(IrActions, self).get_bindings(model_name)
        lst = result.get('report')
        if lst:
            for item in lst:
                reports = self.env['ir.actions.report'].sudo().search([('report_name', '=', item.get('report_name'))])
                if reports:
                    for report in reports:
                        skip_report = False
                        for user in report.hide_user_ids:
                            if user.id == self._uid:
                                skip_report = True
                                break
                        for group in report.hide_group_ids:
                            for user in group.users:
                                if user.id == self._uid:
                                    skip_report = True
                                    break
                        if skip_report:
                            lst.remove(item)
            result.update({'report': lst})
        return result
