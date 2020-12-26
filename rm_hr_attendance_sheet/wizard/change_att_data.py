import time
import pytz
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo import SUPERUSER_ID
from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning
from odoo.tools import float_compare
import odoo.addons.decimal_precision as dp







class attendance_sheet_line_change(models.TransientModel):
    _name = "attendance.sheet.line.change"
    overtime = fields.Float("Overtime")
    late_in = fields.Float("Late In")
    diff_time = fields.Float("Diff Time")
    note = fields.Text("Note",required=True)
    att_line_id=fields.Many2one(comodel_name="attendance.sheet.line")

    @api.model
    def default_get(self, fields):
        res = super(attendance_sheet_line_change, self).default_get(fields)
        atts_line_id = self.env[self._context['active_model']].browse(self._context['active_id'])
        if 'overtime' in fields and 'overtime' not in res:
            res['overtime'] = atts_line_id.overtime
            res['late_in'] = atts_line_id.late_in
            res['diff_time'] = atts_line_id.diff_time
            res['att_line_id'] = atts_line_id.id
        return res


    def change_att_data(self):
        [data]=self.read()
        self.ensure_one()
        atts_line_id = self.env['attendance.sheet.line'].browse(self._context['active_id'])
        res={
            'overtime':data['overtime'],
            'late_in':data['late_in'],
            'diff_time':data['diff_time'],
            'note': data['note'],

        }
        atts_line_id.write(res)
        # atts_line_id.att_sheet_id.calculate_att_data()
        return {'type': 'ir.actions.act_window_close'}
