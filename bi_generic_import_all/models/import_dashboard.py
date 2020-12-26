from odoo import models, fields, api
from datetime import datetime

class import_dashboard_inheirt(models.Model):
    _inherit = 'import.dashboard'


    def _count(self):
        res = super(import_dashboard_inheirt, self)._count()
        for count in self:
            task_obj = self.env['project.task']
            pos_obj = self.env['pos.order']
            attendace_obj = self.env['hr.attendance']
            statement_obj = self.env['account.bank.statement']
            move_obj = self.env['account.move']
            if count.state == 'project.task':
                import_count = task_obj.sudo().search_count([('is_import','=',True)])
                count.import_data = import_count
            # elif count.state == 'pos.order':
            #     import_count = pos_obj.sudo().search_count([('is_import','=',True)])
            #     count.import_data = import_count                
            elif count.state == 'hr.attendance':
                import_count = attendace_obj.sudo().search_count([('is_import','=',True)])
                count.import_data = import_count
            elif count.state == 'account.bank.statement':
                import_count = statement_obj.sudo().search_count([('is_import','=',True)])
                count.import_data = import_count
            elif count.state == 'account.move.journal':
                import_count = move_obj.sudo().search_count([('is_import','=',True),('type', '=', 'entry')])
                count.import_data = import_count
        return res

    state = fields.Selection(selection_add=[
                                            ('pos.order', 'POS order'),
                                            ('project.task', 'Task'),
                                            ('hr.attendance', 'Attendance'),
                                            ('account.bank.statement', 'Bank Statement'),
                                            ('account.move.journal', 'Attendance')])
