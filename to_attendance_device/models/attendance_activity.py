from odoo import models, fields, api


class AttendanceActivity(models.Model):
    _name = 'attendance.activity'
    _description = 'Attendance Activity'

    name = fields.Char(string='Name', required=True, translate=True,
                              help='The name of the attendance activity. E.g. Normal Working, Overtime, etc')

    attendance_status_ids = fields.One2many('attendance.state', 'activity_id', string='Attendance Status',
                                            help='The check-in and check-out statuses of this activity')

    status_count = fields.Integer(string='Status Count', compute='_compute_status_count')

    _sql_constraints = [
        ('unique_name',
         'UNIQUE(name)',
         "The Name of the attendance activity must be unique!"),
    ]

    @api.depends('attendance_status_ids')
    def _compute_status_count(self):
        for r in self:
            r.status_count = len(r.attendance_status_ids)

    def getAttendance(self, device_id=None, user_id=None):
        domain = [('attendance_state_id', 'in', self.mapped('attendance_status_ids').ids)]
        if device_id:
            domain += [('device_id', '=', device_id.id)]

        if user_id:
            domain += [('user_id', '=', user_id.id)]

        return self.env['user.attendance'].search(domain)
