from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

import logging

_logger = logging.getLogger(__name__)


class AttendanceWizard(models.TransientModel):
    _name = 'attendance.wizard'
    _description = 'Attendance Wizard'

    @api.model
    def _get_all_device_ids(self):
        all_devices = self.env['attendance.device'].search([('state', '=', 'confirmed')])
        if all_devices:
            return all_devices.ids
        else:
            return []

    device_ids = fields.Many2many('attendance.device', string='Devices', default=_get_all_device_ids, domain=[('state', '=', 'confirmed')])
    fix_attendance_valid_before_synch = fields.Boolean(string='Fix Attendance Valid', help="If checked, Odoo will recompute all attendance data for their valid"
                                                     " before synchronizing with HR Attendance (upon you hit the 'Synchronize Attendance' button)")

    @api.multi
    def download_attendance_manually(self):
        if not self.device_ids:
            raise UserError(_('You must select at least one device to continue!'))
        self.device_ids.action_attendance_download()

    @api.multi
    def download_device_attendance(self):
        devices = self.env['attendance.device'].search([('state', '=', 'confirmed')])
        devices.action_attendance_download()

    def cron_sync_attendance(self):
        self.with_context(synch_ignore_constraints=True).sync_attendance()

    @api.multi
    def sync_attendance(self):
        """
        This method will synchronize all downloaded attendance data with Odoo attendance data.
        It do not download attendance data from the devices.
        """
        if self.fix_attendance_valid_before_synch:
            self.action_fix_user_attendance_valid()

        synch_ignore_constraints = self.env.context.get('synch_ignore_constraints', False)

        error_msg = {}
        HrAttendance = self.env['hr.attendance'].with_context(synch_ignore_constraints=synch_ignore_constraints)

        activity_ids = self.env['attendance.activity'].search([])

        DeviceUserAttendance = self.env['user.attendance']

        last_employee_attendance = {}
        for activity_id in activity_ids:
            if activity_id.id not in last_employee_attendance.keys():
                last_employee_attendance[activity_id.id] = {}

            unsync_data = DeviceUserAttendance.search([('hr_attendance_id', '=', False),
                                                       ('valid', '=', True),
                                                       ('employee_id', '!=', False),
                                                       ('activity_id', '=', activity_id.id)], order='timestamp ASC')
            for att in unsync_data:
                employee_id = att.user_id.employee_id
                if employee_id.id not in last_employee_attendance[activity_id.id].keys():
                    last_employee_attendance[activity_id.id][employee_id.id] = False

                if att.type == 'checkout':
                    # find last attendance
                    last_employee_attendance[activity_id.id][employee_id.id] = HrAttendance.search(
                        [('employee_id', '=', employee_id.id),
                         ('activity_id', 'in', (activity_id.id, False)),
                         ('check_in', '<=', att.timestamp)], limit=1, order='check_in DESC')

                    hr_attendance_id = last_employee_attendance[activity_id.id][employee_id.id]

                    if hr_attendance_id:
                        try:
                            hr_attendance_id.with_context(synch_ignore_constraints=synch_ignore_constraints).write({
                                'check_out': att.timestamp,
                                'checkout_device_id': att.device_id.id
                                })
                        except ValidationError as e:
                            if att.device_id not in error_msg:
                                error_msg[att.device_id] = ""

                            msg = ""
                            att_check_time = fields.Datetime.context_timestamp(att, att.timestamp)
                            msg += str(e) + "<br />"
                            msg += _("'Check Out' time cannot be earlier than 'Check In' time. Debug information:<br />"
                                          "* Employee: <strong>%s</strong><br />"
                                          "* Type: %s<br />"
                                          "* Attendance Check Time: %s<br />") % (employee_id.name, att.type, fields.Datetime.to_string(att_check_time))
                            _logger.error(msg)
                            error_msg[att.device_id] += msg
                else:
                    # create hr attendance data
                    vals = {
                        'employee_id': employee_id.id,
                        'check_in': att.timestamp,
                        'checkin_device_id': att.device_id.id,
                        'activity_id': activity_id.id,
                        }
                    hr_attendance_id = HrAttendance.search([
                        ('employee_id', '=', employee_id.id),
                        ('check_in', '=', att.timestamp),
                        ('checkin_device_id', '=', att.device_id.id),
                        ('activity_id', '=', activity_id.id)], limit=1)
                    if not hr_attendance_id:
                        try:
                            hr_attendance_id = HrAttendance.create(vals)
                        except Exception as e:
                            _logger.error(e)

                if hr_attendance_id:
                    att.write({
                        'hr_attendance_id': hr_attendance_id.id
                        })

        if bool(error_msg):
            for device in error_msg.keys():

                if not device.debug_message:
                    continue
                device.message_post(body=error_msg[device])

    @api.multi
    def clear_attendance(self):
        if not self.device_ids:
            raise (_('You must select at least one device to continue!'))
        if not self.env.user.has_group('hr_attendance.group_hr_attendance_manager'):
            raise UserError(_('Only HR Attendance Managers can manually clear device attendance data'))

        for device in self.device_ids:
                device.clearAttendance()

    @api.multi
    def action_fix_user_attendance_valid(self):
        self.ensure_one()
        all_attendances = self.env['user.attendance'].search([])
        for attendance in all_attendances:
            if attendance.is_valid():
                attendance.write({'valid': True})
            else:
                attendance.write({'valid': False})
