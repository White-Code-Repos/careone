import pytz
import time
import logging

from datetime import datetime

from odoo import models, fields, api, _
from odoo.addons.mail.models import mail_template
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression

from ..pyzk.zk import ZK
from ..pyzk.zk.exception import TimeoutError

_logger = logging.getLogger(__name__)


class AttendanceDevice(models.Model):
    _name = 'attendance.device'
    _description = 'Attendance Device'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'to.base']

    def _get_default_attendance_states(self):
        att_state_ids = self.env['attendance.state']

        # Normal Working Attendance
        attendance_device_state_code_0 = self.env.ref('to_attendance_device.attendance_device_state_code_0')
        if attendance_device_state_code_0:
            att_state_ids += attendance_device_state_code_0
        attendance_device_state_code_1 = self.env.ref('to_attendance_device.attendance_device_state_code_1')
        if attendance_device_state_code_1:
            att_state_ids += attendance_device_state_code_1

        # Overtime Working Attendance
        attendance_device_state_code_4 = self.env.ref('to_attendance_device.attendance_device_state_code_4')
        if attendance_device_state_code_4:
            att_state_ids += attendance_device_state_code_4
        attendance_device_state_code_5 = self.env.ref('to_attendance_device.attendance_device_state_code_5')
        if attendance_device_state_code_5:
            att_state_ids += attendance_device_state_code_5
        return att_state_ids

    @api.model
    def _get_default_attendance_device_state_lines(self):
        attendance_device_state_line_data = []
        for state in self._get_default_attendance_states():
            attendance_device_state_line_data.append(
                (0, 0, {
                    'attendance_state_id': state.id,
                    'code': state.code,
                    'type': state.type,
                    'activity_id': state.activity_id.id
                    })
                )
        return attendance_device_state_line_data

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled')
        ], string='Status', default='draft', index=True, copy=False, required=True, track_visibility='onchange')

    name = fields.Char(string="Name", required=True, help='The name of the attendance device', track_visibility='onchange', translate=True, copy=True, default='/',
                       readonly=True, states={'draft': [('readonly', False)]})

    firmware_version = fields.Char(string='Firmware Version', readonly=True,
                                   help="The firmware version of the device which will be filled automatically when you hit the 'Get Device Info' button.")
    serialnumber = fields.Char(string='Serial Number', readonly=True,
                               help="The serial number of the device which will be filled automatically when you hit the 'Get Device Info' button.")
    oem_vendor = fields.Char(string='OEM Vendor', readonly=True,
                               help="The OEM Vendor of the device which will be filled automatically when you hit the 'Get Device Info' button.")
    platform = fields.Char(string='Platform', readonly=True,
                               help="The Platform of the device which will be filled automatically when you hit the 'Get Device Info' button.")
    fingerprint_algorithm = fields.Char(string='Fingerprint Algorithm', readonly=True,
                               help="The Fingerprint Algorithm (aka ZKFPVersion) of the device which will be filled automatically when you hit the 'Get Device Info' button.")
    device_name = fields.Char(string='Device Name', readonly=True,
                               help="The model of the device which will be filled automatically when you hit the 'Get Device Info' button.")

    work_code = fields.Char(string='Work Code', readonly=True,
                               help="The Work Code of the device which will be filled automatically when you hit the 'Get Device Info' button.")

    ip = fields.Char(string="IP / Domain Name", required=True, track_visibility='onchange', copy=False, readonly=True, states={'draft': [('readonly', False)]},
                     help='The accessible IP or Domain Name of the device to get device\'s attendance data', default='0.0.0.0')
    port = fields.Integer(string="Port", required=True, default=4370, track_visibility='onchange', readonly=True, states={'draft': [('readonly', False)]})
    timeout = fields.Integer(string='Timeout', default=20, required=True, help='Connection Timeout in second', track_visibility='onchange',
                             readonly=True, states={'draft': [('readonly', False)]})
    description = fields.Text(string="Description")
    user_id = fields.Many2one('res.users', string="Technician", track_visibility='onchange', default=lambda self: self.env.user)
    device_user_ids = fields.One2many('attendance.device.user', 'device_id', string='Device Users',
                                      help='List of Users stored in the attendance device')
    device_users_count = fields.Integer(string='Users Count', compute='_compute_device_users_count', store=True)

    mapped_employee_ids = fields.Many2many('hr.employee', 'mapped_device_employee_rel', string='Mapped Employees',
                                           compute='_compute_employees', store=True,
                                           help="List of employees that have been mapped with this device's users")

    mapped_employees_count = fields.Integer(string='Mapped Employee Count', compute='_compute_mapped_employees_count', store=True)

    umapped_device_user_ids = fields.One2many('attendance.device.user', 'device_id', string='Device Users',
                                              domain=[('employee_id', '=', False)],
                                              help='List of Device Users that have not been mapped with an employee')

    unmapped_employee_ids = fields.Many2many('hr.employee', 'device_employee_rel', 'device_id', 'employee_id',
                                             compute='_compute_employees', store=True, string='Unmapped Employees',
                                             help="The employees that have not been mapped with any user of this device")

    attendance_device_state_line_ids = fields.One2many('attendance.device.state.line', 'device_id', string='State Codes', copy=False,
                                                       default=_get_default_attendance_device_state_lines,
                                                       readonly=True, states={'draft': [('readonly', False)]})
    location_id = fields.Many2one('attendance.device.location', string='Location', track_visibility='onchange',
                                  help='The location where the device is located', required=True,
                                  readonly=True, states={'draft': [('readonly', False)]})

    ignore_unknown_code = fields.Boolean(string='Ignore Unknown Code', default=False, track_visibility='onchange',
                                         help='Sometimes you don\'t want to load attendance data with status '
                                         'codes those not declared in the table below. In such the case, check this field.',
                                         readonly=True, states={'draft': [('readonly', False)]})

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id,
                                 readonly=True, states={'draft': [('readonly', False)]})

    auto_clear_attendance = fields.Boolean(string='Auto Clear Attendance Data', default=False, track_visibility='onchange',
                                            oldname='auto_clear_atttendance',
                                            readonly=True, states={'draft': [('readonly', False)]},
                                            help='Check this to clear all device attendance data after download into Odoo')

    auto_clear_attendance_schedule = fields.Selection([
        ('on_download_complete', 'On Download Completion'),
        ('time_scheduled', 'Time Scheduled')], string='Auto Clear Schedule', required=True, default='on_download_complete', track_visibility='onchange',
        help="On Download Completion: Delete attendance data as soon as download finished\n"
        "Time Scheduled: Delete attendance data on the time specified below")
    auto_clear_attendance_hour = fields.Float(string='Auto Clear At', track_visibility='onchange', required=True, default=0.0,
                                               help="The time (in the attendance device's timezone) to clear attendance data after download.")

    auto_clear_attendance_dow = fields.Selection([
        (-1, 'Everyday'),
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'), ], string='Auto Clear On', default=-1, required=True, track_visibility='onchange')

    auto_clear_attendance_error_notif = fields.Boolean(string='Auto Clear Attendance Notif.', default=True,
                                                        oldname='auto_clear_atttendance_error_notif', track_visibility='onchange',
                                                        help='Notify upon no safe found to clear attendance data')

    tz = fields.Selection('_tz_get', string='Time zone', default=lambda self: self.env.context.get('tz') or self.env.user.tz, track_visibility='onchange',
                          required=True, readonly=True, states={'draft': [('readonly', False)]},
                          help="The device's timezone, used to output proper date and time values "
                               "inside attendance reports. It is important to set a value for this field.")

    active = fields.Boolean(string='Active', default=True, track_visibility='onchange', readonly=True, states={'draft': [('readonly', False)]})
    unique_uid = fields.Boolean(string='Unique UID', default=True, required=True, track_visibility='onchange',
                                readonly=True, states={'draft': [('readonly', False)]},
                                help='Some Bad Devices allow uid duplication. In this case, uncheck this field. But it is recommended to change your device.')
    last_attendance_download = fields.Datetime(string='Last Sync.', readonly=True,
                                               help='The last time that the attendance data was downlowed from the device into Odoo.')

    map_before_dl = fields.Boolean(string='Map Employee Before Download', default=True,
                                   help='Always try to map users and employees (if any new found) before downloading attendance data.')
    create_employee_during_mapping = fields.Boolean(string='Create Employees During Mapping', default=False,
                                                    help="If checked, during mapping between Device's Users and company's employees, umapped device"
                                                    " users will try to create a new employee then map accordingly.")

    download_error_notification = fields.Boolean(string='Download Error Notification', default=True,
                                                 readonly=True, states={'draft': [('readonly', False)]},
                                                 help='Enable this to get notified when data download error occurs.')
    debug_message = fields.Boolean(string='Debug Message', default=False, help="If checked, debugging messages will be posted in"
                                   " OpenChatter for debugging purpose")

    user_attendance_ids = fields.One2many('user.attendance', 'device_id', string='Attendance Data', readonly=True)
    total_att_records = fields.Integer(string='Attendance Records', compute='_compute_total_attendance_records')
    finger_template_ids = fields.One2many('finger.template', 'device_id', string='Finger Template', readonly=True)
    total_finger_template_records = fields.Integer(string='Finger Templates', compute='_compute_total_finger_template_records')
    protocol = fields.Selection([('udp', 'UDP'), ('tcp', 'TCP')], string='Protocol', required=True, default='tcp',
                                track_visibility='onchange',
                                help="Some old devices do not support TCP. In such the case, please try on switching to UDP.")
    omit_ping = fields.Boolean(string='Omit Ping', default=True, help='Omit ping ip address when connecting to device.',
                               readonly=True, states={'draft': [('readonly', False)]})
    password = fields.Char(string='Password', readonly=True, states={'draft': [('readonly', False)]},
                           help="The password to authenticate the device, if required")

    unaccent_user_name = fields.Boolean(string='Unaccent User Name', default=True, track_visibility='onchange',
                                        help="Some Devices support Unicode names such as, some others do not."
                                        " In addition to this, the name field on the device is usually limited at about 24 Latin characters"
                                        " or less Unicode characters. Unaccent is sometimes a workaround for long Unicode names")

    zk = None
    zk_cache = {}

    _sql_constraints = [
        ('ip_and_port_unique',
         'UNIQUE(ip, port, location_id)',
         "You cannot have more than one device with the same ip and port of the same location!"),
    ]

    @api.model
    def _set_zk(self):
        """
        This method return a ZK object.
        If an object corresponding to the connection param was created
        and available in self.zk_cache, it will be return. To avoid it, call it with .with_context(no_zk_cache=True)        
        """
        force_udp = self.protocol == 'udp'
        password = self.password or 0
        cached_key = self.protocol + str(self.omit_ping) + str(self.timeout) + str(password)
        if self.ip:
            cached_key += self.ip
        if self.port:
            cached_key += str(self.port)

        if not cached_key in self.zk_cache.keys() or self.env.context.get('no_zk_cache', False):
            self.zk_cache[cached_key] = ZK(self.ip, self.port, self.timeout, password=password, force_udp=force_udp, ommit_ping=self.omit_ping)

        self.zk = self.zk_cache[cached_key]

    @api.model
    def _tz_get(self):
        return [(x, x) for x in pytz.all_timezones]

    @api.onchange('location_id')
    def _onchange_location_id(self):
        if self.location_id and self.location_id.tz:
            self.tz = self.location_id.tz

    @api.multi
    def name_get(self):
        """
        name_get that supports displaying location name and model as prefix
        """
        result = []
        for r in self:
            name = r.name
            if r.oem_vendor:
                if r.device_name:
                    name = '[' + r.oem_vendor + ' ' + r.device_name + '] ' + name
                else:
                    name = '[' + r.oem_vendor + '] ' + name

            if r.location_id:
                name = '[' + r.location_id.name + '] ' + name

            result.append((r.id, name))
        return result

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        """
        name search that supports searching by tag code
        """
        args = args or []
        domain = []
        if name:
            domain = ['|', ('location_id.name', '=ilike', name + '%'), ('name', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&'] + domain
        state = self.search(domain + args, limit=limit)
        return state.name_get()

    @api.depends('device_user_ids', 'device_user_ids.active')
    def _compute_device_users_count(self):
        total_att_data = self.env['attendance.device.user'].read_group([('device_id', 'in', self.ids)], ['device_id'], ['device_id'])
        mapped_data = dict([(dict_data['device_id'][0], dict_data['device_id_count']) for dict_data in total_att_data])
        for r in self:
            r.device_users_count = mapped_data.get(r.id, 0)

    @api.multi
    def _compute_total_finger_template_records(self):
        total_att_data = self.env['finger.template'].read_group([('device_id', 'in', self.ids)], ['device_id'], ['device_id'])
        mapped_data = dict([(dict_data['device_id'][0], dict_data['device_id_count']) for dict_data in total_att_data])
        for r in self:
            r.total_finger_template_records = mapped_data.get(r.id, 0)

    @api.multi
    def _compute_total_attendance_records(self):
        total_att_data = self.env['user.attendance'].read_group([('device_id', 'in', self.ids)], ['device_id'], ['device_id'])
        mapped_data = dict([(dict_data['device_id'][0], dict_data['device_id_count']) for dict_data in total_att_data])
        for r in self:
            r.total_att_records = mapped_data.get(r.id, 0)

    @api.depends('device_user_ids', 'device_user_ids.active', 'device_user_ids.employee_id', 'device_user_ids.employee_id.active')
    def _compute_employees(self):
        HrEmployee = self.env['hr.employee']
        for r in self:
            r.update({
                'unmapped_employee_ids':[(6, 0, HrEmployee.search([('id', 'not in', r.device_user_ids.mapped('employee_id').ids)]).ids)],
                'mapped_employee_ids': [(6, 0, r.device_user_ids.mapped('employee_id').filtered(lambda employee: employee.active == True).ids)],
                })

    @api.depends('mapped_employee_ids')
    def _compute_mapped_employees_count(self):
        for r in self:
            r.mapped_employees_count = len(r.mapped_employee_ids)

    @api.onchange('unique_uid')
    def onchange_unique_uid(self):
        if not self.unique_uid:
            raise UserError(_('This is for experiment to check if the device contains bad data with non-unique user\'s uid.'
                              ' Turn this option off will allow mapping device user\'s user_id with user\'s user_id in Odoo.\n'
                              'NOTE:\n'
                              '- non-latin user_id are not supportted.\n'
                              '- Do not turn this option off in production.'))

    @api.model
    def create(self, vals):
        if 'ip' in vals:
            vals['ip'] = vals['ip'].strip()
        return super(AttendanceDevice, self).create(vals)

    @api.multi
    def write(self, vals):
        if 'ip' in vals:
            vals['ip'] = vals['ip'].strip()
        return super(AttendanceDevice, self).write(vals)

    @api.model
    def connect(self, retry=1):

        def post_message():
            email_template_id = self.env.ref('to_attendance_device.email_template_attendance_device')
            self.post_message(email_template_id)
            self.env.cr.commit()

        try:
            self._set_zk()
            return self.zk.connect()
        except TimeoutError as e:
            post_message()
            raise ValidationError(_("Could not get connected to the device %s due to timeout error."
                                    " This is usually due to either the network error or wrong protocol selection or password authentication is required.")
                                    % (self.display_name,))

        except Exception as e:
            while retry > 0:
                retry -= 1
                # we don't want to use zk_cache when retrying
                # we ask for new ZK object
                return self.with_context(no_zk_cache=True).connect(retry=retry)
            post_message()
            raise ValidationError(_("Could not get connected to the device '%s'. Please check your network"
                                    " configuration and device password and/or hard restart your device") % (self.display_name,))

    def disconnect(self):
        res = False
        try:
            res = self.zk.disconnect()
        except Exception:
            raise ValidationError(_('Could not get the device %s disconnected') % (self.display_name,))
        finally:
            return res

    def disableDevice(self):
        """
        disable (lock) device, ensure no activity when process run
        """
        res = False
        try:
            res = self.zk.disable_device()
        except Exception:
            raise ValidationError(_('Could not get the device %s disabled') % (self.display_name,))
        finally:
            return res

    @api.multi
    def action_restart(self):
        self.ensure_one()
        self.restartDevice()

    def enableDevice(self):
        """
        re-enable the connected device
        """
        res = False
        try:
            res = self.zk.enable_device()
        except Exception:
            raise ValidationError(_('Could not get the device %s re-enabled') % (self.display_name,))
        finally:
            return res

    def getFirmwareVersion(self):
        '''
        return the firmware version
        '''
        try:
            self.connect()
            self.enableDevice()
            return self.zk.get_firmware_version()
        except Exception:
            raise ValidationError(_('Could not get the firmware version of the device %s') % (self.display_name,))
        finally:
            self.disconnect()

    def getSerialNumber(self):
        '''
        return the serial number
        '''
        try:
            self.connect()
            self.enableDevice()
            return self.zk.get_serialnumber()
        except Exception:
            raise ValidationError(_('Could not get the serial number of the device %s') % (self.display_name,))
        finally:
            self.disconnect()

    def getOEMVendor(self):
        '''
        return the serial number
        '''
        try:
            self.connect()
            self.enableDevice()
            return self.zk.get_oem_vendor()
        except Exception:
            raise ValidationError(_('Could not get the OEM Vendor of the device %s') % (self.display_name,))
        finally:
            self.disconnect()

    def getFingerprintAlgorithm(self):
        '''
        return the Fingerprint Algorithm
        '''
        try:
            self.connect()
            self.enableDevice()
            return self.zk.get_fingerprint_algorithm()
        except Exception:
            raise ValidationError(_('Could not get the Fingerprint Algorithm of the device %s') % (self.display_name,))
        finally:
            self.disconnect()

    def getPlatform(self):
        '''
        return the serial number
        '''
        try:
            self.connect()
            self.enableDevice()
            return self.zk.get_platform()
        except Exception:
            raise ValidationError(_('Could not get the Platform of the device %s') % (self.display_name,))
        finally:
            self.disconnect()

    def getDeviceName(self):
        '''
        return the serial number
        '''
        try:
            self.connect()
            self.enableDevice()
            return self.zk.get_device_name()
        except Exception:
            raise ValidationError(_('Could not get the Name of the device %s') % (self.display_name,))
        finally:
            self.disconnect()

    def getWorkCode(self):
        '''
        return the serial number
        '''
        try:
            self.connect()
            self.enableDevice()
            return self.zk.get_workcode()
        except Exception:
            raise ValidationError(_('Could not get the Work Code of the device %s') % (self.display_name,))
        finally:
            self.disconnect()

    def restartDevice(self):
        '''
        restart the device
        '''
        res = False
        try:
            self.connect()
            self.enableDevice()
            res = self.zk.restart()
        except Exception:
            raise ValidationError(_('Could not get the serial number of the device %s') % (self.display_name,))
        finally:
            return res

    def setUser(self, uid, name, privilege, password, group_id, user_id):
        try:
#             uid = uid + uid_increment
            self.connect()
            self.enableDevice()
            self.disableDevice()

            return self.zk.set_user(uid, name, privilege, password, group_id, user_id)
        except Exception as e:
            _logger.info(e)
            raise ValidationError(_('Could not set user into the device %s. Here are the user information:\n'
                                    'uid: %s\n'
                                    'name: %s\n'
                                    'privilege: %s\n'
                                    'password: %s\n'
                                    'group_id: %s\n'
                                    'user_id: %s\n')
                                  % (self.display_name, uid, name, privilege, password, group_id, user_id))
        finally:
            self.enableDevice()
            self.disconnect()

    def delUser(self, uid, user_id):
        '''
        delete specific user by uid
        '''
        try:
            self.connect()
            self.enableDevice()
            self.disableDevice()
            return self.zk.delete_user(uid, user_id)
        except Exception as e:
            raise ValidationError(_('Could not delete the user with uid "%s", user_id "%s" from the device %s\n%s') % (uid, user_id, self.display_name, e))
        finally:
            self.enableDevice()
            self.disconnect()

    def action_clear_data(self):
        '''
        clear all data (include: user, attendance report, finger database )
        '''
        try:
            self.connect()
            self.enableDevice()
            self.disableDevice()
            return self.zk.clear_data()
        except Exception:
            raise ValidationError(_('Could not clear data from the device %s') % (self.display_name,))
        finally:
            self.enableDevice()
            self.disconnect()

    def getUser(self, tries=3):
        '''
        return a Python List of device users in User(uid, name, privilege, password, group_id, user_id)
        '''
        try:
            self.connect()
            self.enableDevice()
            self.disableDevice()
            return self.zk.get_users()
        except Exception as e:
            _logger.error(str(e))
            if tries > 0:
                tries -= 1
                self.enableDevice()
                self.disconnect()
                time.sleep(0.5)
                return self.getUser(tries)
            raise ValidationError(_('Could not get users from the device %s\n'
                                    'If you had connected to your device, perhaps your device had problem. '
                                    'Some bad devices allowed duplicated uid may cause such problem. In such case, '
                                    'if you still want to load users from that bad device, please uncheck Data '
                                    'Acknowledge field.') % (self.display_name,))
        finally:
            self.enableDevice()
            self.disconnect()

    def setFingerTemplate(self, uid, name, privilege, password, group_id, user_id, fingers):
        try:
#             uid = uid + uid_increment
            self.connect()
            self.enableDevice()
            self.disableDevice()

            return self.zk.save_user_template(uid, name, privilege, password, group_id, user_id, fingers)
        except Exception as e:
            _logger.info(e)
            raise ValidationError(_('Could not set finger template into the device %s. Here are the information:\n'
                                    'user_id: %s\n')
                                  % (self.display_name, user_id))
        finally:
            self.enableDevice()
            self.disconnect()

    def delFingerTemplate(self, uid, fid, user_id):
        '''
        delete finger template by uid and fid
        '''
        try:
            self.connect()
            self.enableDevice()
            self.disableDevice()
            return self.zk.delete_user_template(uid, fid, user_id)
        except Exception as e:
            raise ValidationError(_('Could not delete finger template with fid "%s" of uid "%s" from the device %s') % (fid, uid, self.display_name,))
        finally:
            self.enableDevice()
            self.disconnect()

    def getFingerTemplate(self, tries=3):
        '''
        return a Python List of fingers template in Finger(uid, fid, valid, template)
        '''
        try:
            self.connect()
            self.enableDevice()
            self.disableDevice()
            return self.zk.get_templates()
        except Exception as e:
            _logger.error(str(e))
            if tries > 0:
                tries -= 1
                self.enableDevice()
                self.disconnect()
                time.sleep(0.5)
                return self.getFingerTemplate(tries)
            raise ValidationError(_('Could not get finger templates from the device %s\n'
                                    'If you had connected to your device, perhaps your device had problem. '
                                    'Some bad devices allowed duplicated uid may cause such problem. In such case, '
                                    'if you still want to load users from that bad device, please uncheck Data '
                                    'Acknowledge field.') % (self.display_name,))
        finally:
            self.enableDevice()
            self.disconnect()

    def getMaxUid(self):
        '''
        return max uid of users on attendance device
        '''
        try:
            self.connect()
            self.enableDevice()
            self.disableDevice()
            return self.zk.get_max_uid()
        except Exception as e:
            _logger.error(str(e))
            raise ValidationError(_('Could not get max uid from the device %s\n'
                                    'If you had connected to your device, perhaps your device had problem. ') % (self.display_name,))
        finally:
            self.enableDevice()
            self.disconnect()

    def clearData(self):
        '''
        clear all data (include: user, attendance report, finger database )
        '''
        try:
            self.connect()
            self.enableDevice()
            return self.zk.clear_data()
        except Exception:
            raise ValidationError(_('Could not clear all data from the device %s') % (self.display_name,))
        finally:
            self.enableDevice()
            self.disconnect()

    def getAttendance(self, tries=3):
        post_err_msg = False
        try:
            self.connect()
            self.enableDevice()
            self.disableDevice()
            return self.zk.get_attendance()

        except Exception as e:
            _logger.error(str(e))
            if tries > 0:
                tries -= 1
                self.enableDevice()
                self.disconnect()
                time.sleep(0.5)
                return self.getAttendance(tries)
            post_err_msg = True
            raise ValidationError(_('Could not get attendance data from the device %s') % (self.display_name,))

        finally:
            if post_err_msg and self.download_error_notification:
                email_template_id = self.env.ref('to_attendance_device.email_template_error_get_attendance')
                self.post_message(email_template_id)
            self.enableDevice()
            self.disconnect()

    def clearAttendance(self):
        '''
        clear all attendance records from the device
        '''
        try:
            self.connect()
            self.enableDevice()
            self.disableDevice()
            return self.zk.clear_attendance()
        except Exception:
            raise ValidationError(_('Could not get attendance data from the device %s') % (self.display_name,))
        finally:
            self.enableDevice()
            self.disconnect()

    @api.multi
    def _download_users_by_uid(self):
        """
        This method download and update all device users into model attendance.device.user using uid as key
        """
        DeviceUser = self.env['attendance.device.user']
        for r in self:
            error_msg = ""
            # device_users = User(uid, name, privilege, password, group_id, user_id)
            device_users = r.getUser()

            uids = []
            for device_user in device_users:
                uids.append(device_user.uid)

            existing_user_ids = []

            device_user_ids = DeviceUser.search([('device_id', '=', r.id), '|', ('active', '=', True), ('active', '=', False)])
            for user in device_user_ids.filtered(lambda user: user.uid in uids):
                existing_user_ids.append(user.uid)

            for device_user in device_users:
                uid = device_user.uid
                vals = {
                    'uid': uid,
                    'name': device_user.name,
                    'privilege': device_user.privilege,
                    'password': device_user.password,
                    'user_id': device_user.user_id,
                    'device_id': r.id,
                    }
                if device_user.group_id.isdigit():
                    vals['group_id'] = device_user.group_id
                if uid not in existing_user_ids:
                    try:

                        DeviceUser.create(vals)
                    except Exception as e:
                        _logger.info(e)
                        _logger.info(vals)
                        error_msg += str(e)
                        error_msg += _("\nData that caused the error: %s" % (str(vals)))
                else:
                    existing = DeviceUser.search([('uid', '=', uid), ('device_id', '=', r.id), '|', ('active', '=', True), ('active', '=', False)], limit=1)
                    if existing:
                        update_data = {}
                        if existing.name != vals['name']:
                            update_data['name'] = vals['name']
                        if existing.privilege != vals['privilege']:
                            update_data['privilege'] = vals['privilege']
                        if existing.password != vals['password']:
                            update_data['password'] = vals['password']
                        if 'group_id' in vals and existing.group_id != vals['group_id']:
                            update_data['group_id'] = vals['group_id']
                        if existing.user_id != vals['user_id']:
                            update_data['user_id'] = vals['user_id']
                        if existing.device_id.id != vals['device_id']:
                            update_data['device_id'] = vals['device_id']
                        if bool(update_data):
                            try:
                                existing.write(update_data)
                            except Exception as e:
                                _logger.info(e)
                                _logger.info(vals)
                                error_msg += str(e) + "<br />"
                                error_msg += _("\nData that caused the error: %s" % (str(update_data))) + "<br />"
            if error_msg and r.debug_message:
                r.message_post(body=error_msg)

    @api.multi
    def _download_users_by_user_id(self):
        """
        This method download and update all device users into model attendance.device.user using user_id as key
        NOTE: This method is experimental as it failed on comparing user_id in unicode type from devices (unicode: string) with user_id in unicode string from Odoo (u'string')
        """
        DeviceUser = self.env['attendance.device.user']
        for r in self:
            # device_users = User(uid, name, privilege, password, group_id, user_id)
            device_users = r.getUser()

            user_ids = []
            for device_user in device_users:
                user_ids.append(str(device_user.user_id))

            existing_user_ids = []
            device_user_ids = DeviceUser.search([('device_id', '=', r.id), '|', ('active', '=', True), ('active', '=', False)])
            for user in device_user_ids.filtered(lambda user: user.user_id in user_ids):
                existing_user_ids.append(str(user.user_id))

            for device_user in device_users:
                uid = device_user.uid
                name = device_user.name
                privilege = device_user.privilege
                password = device_user.password
                group_id = device_user.group_id
                user_id = str(device_user.user_id)
                vals = {
                    'uid': uid,
                    'name': name,
                    'privilege': privilege,
                    'password': password,
                    'group_id': group_id,
                    'user_id': user_id,
                    'device_id': r.id,
                    }
                if user_id not in existing_user_ids:
                    DeviceUser.create(vals)
                else:
                    existing = DeviceUser.search([
                        ('user_id', '=', user_id),
                        ('device_id', '=', r.id),
                        '|',
                            ('active', '=', True),
                            ('active', '=', False)], limit=1)
                    if existing:
                        existing.write(vals)

    @api.multi
    def action_user_download(self):
        """
        This method download and update all device users into model attendance.device.user
        """
        for r in self:
            if r.unique_uid:
                r._download_users_by_uid()
            else:
                r._download_users_by_user_id()

    @api.multi
    def action_user_upload(self):
        """
        This method will
        1. Download users from device
        2. Map the users with emloyee
        3. Upload users from model attendance.device.user into the device
        """
        ignored_employees_dict = {}
        for r in self:
            # Then we download and map all employees with users
            r.action_employee_map()
            # Then we create users from unmapped employee
            ignored_employees = []
            for employee in r.unmapped_employee_ids:
                if not employee.barcode:
                    ignored_employees.append(employee)
                    continue
                employee.action_load_to_attendance_device(r)
            # we download and map all employees with users again
            r.action_employee_map()

            if len(ignored_employees) > 0:
                ignored_employees_dict[r] = ignored_employees

        if not bool(ignored_employees_dict):
            message = _('The following employees, who have no Badge ID defined, have not been uploaded to the corresponding device:\n')
            for device in ignored_employees_dict.keys():
                for employee in ignored_employees_dict[device]:
                    message += device.name + ': ' + employee.name + '\n'

            return {
                'warning': {
                    'title': "Some Employees could not be uploaded!",
                    'message': message,
                },
            }

    @api.multi
    def action_employee_map(self):
        self.action_user_download()

        for r in self:
            for user in r.device_user_ids.filtered(lambda user: not user.employee_id):
                employee = user.smart_find_employee()
                if employee:
                    user.write({
                        'employee_id': employee.id,
                        })

            if r.create_employee_during_mapping:
                for user in r.device_user_ids.filtered(lambda user: not user.employee_id):
                    user.create_employee()

    @api.multi
    def action_attendance_download(self):
        DeviceUserAttendance = self.env['user.attendance']
        AttendanceUser = self.env['attendance.device.user']

        for r in self:
            error_msg = ""
            if r.map_before_dl:
                r.action_finger_template_download()

            attendance_states = {}
            for state_line in r.attendance_device_state_line_ids:
                attendance_states[state_line.attendance_state_id.code] = state_line.attendance_state_id.id

            attendance_data = r.getAttendance()
            for attendance in attendance_data:
                if attendance.punch not in attendance_states.keys():
                    if not r.ignore_unknown_code:
                        raise UserError(_('We found attendance status code "%s" from your device %s '
                                      'but no such code found in the device\'s settings in Odoo. '
                                      'Please go to the device %s and add this attendance code.\n'
                                      'In case you want to ignore to load attendance data with this code, '
                                      ' go to the device setting in Odoo and check "Ignore Unknown Code".')
                                    % (attendance.punch, r.display_name, r.display_name))
                    else:
                        continue

                user_id = AttendanceUser.search([
                    ('user_id', '=', attendance.user_id),
                    ('device_id', '=', r.id),
                    '|',
                        ('active', '=', True),
                        ('active', '=', False)], limit=1)
                if user_id:
                    utc_timestamp = r.convert_time_to_utc(attendance.timestamp, r.tz)

                    duplicate_attend = DeviceUserAttendance.search([
                        ('device_id', '=', r.id),
                        ('user_id', '=', user_id.id),
                        ('timestamp', '=', utc_timestamp)], limit=1)

                    if not duplicate_attend:
                        try:
                            vals = {
                                'device_id': r.id,
                                'user_id': user_id.id,
                                'timestamp': utc_timestamp,
                                'status': attendance.punch,
                                'attendance_state_id': attendance_states[attendance.punch]
                                }

                            DeviceUserAttendance.create(vals)
                        except Exception as e:
                            error_msg += str(e) + "<br />"
                            error_msg += _("Error create DeviceUserAttendance record: device_id %s; user_id %s; timestamp %s; attendance_state_id %s.<br />") % (r.id, user_id.id, mail_template.format_tz(r, attendance.timestamp, r.tz), attendance_states[attendance.punch])
                            _logger.error(error_msg)
                            pass
            r.last_attendance_download = fields.Datetime.now()
            if error_msg and r.debug_message:
                r.message_post(body=error_msg)

            if not r.auto_clear_attendance:
                continue

            if r.auto_clear_attendance_schedule == 'on_download_complete':
                r.action_attendance_clear()
            elif r.auto_clear_attendance_schedule == 'time_scheduled':
                # datetime in the timezone of the device
                dt_now = self.convert_utc_time_to_tz(datetime.utcnow(), r.tz)
                float_dt_now = self.time_to_float_hour(dt_now)

                if r.auto_clear_attendance_dow == -1 or dt_now.weekday() == r.auto_clear_attendance_dow:
                    delta = r.auto_clear_attendance_hour - float_dt_now
                    if abs(delta) <= 0.5 or abs(delta) >= 23.5:
                        r.action_attendance_clear()

    @api.multi
    def action_finger_template_download(self):
        FingerTemplate = self.env['finger.template']
        for r in self:
            r.action_employee_map()

            template_data = r.getFingerTemplate()
            template_datas = []
            for template in template_data:
                template_datas.append(str(template.uid) + '_' + str(template.fid))

            existing_finger_template_ids = []
            finger_template_ids = FingerTemplate.search([('device_id', '=', r.id)])
            for template in finger_template_ids.filtered(lambda tmp: (str(tmp.uid) + '_' + str(tmp.fid)) in template_datas):
                existing_finger_template_ids.append(str(template.uid) + '_' + str(template.fid))

            for template in template_data:
                uid = template.uid
                fid = template.fid
                valid = template.valid
                tmp = template.template
                device_user_id = self.env['attendance.device.user'].search([('uid', '=', uid), ('device_id', '=', r.id)], limit=1)
                if not device_user_id:
                    continue
                vals = {
                    'device_user_id': device_user_id.id,
                    'fid': fid,
                    'valid': valid,
                    'template': tmp,
                    }
                if device_user_id.employee_id:
                    vals['employee_id'] = device_user_id.employee_id.id

                if (str(template.uid) + '_' + str(template.fid)) not in existing_finger_template_ids:
                    FingerTemplate.create(vals)
                else:
                    existing = FingerTemplate.search([
                        ('uid', '=', uid),
                        ('fid', '=', fid),
                        ('device_id', '=', r.id),
                        ], limit=1)
                    if existing:
                        existing.write(vals)
        return

    @api.model
    def is_attendance_clear_safe(self):
        """
        If the data from devices has not been downloaded into Odoo, this method will return false
        """
        UserAttendance = self.env['user.attendance']
        User = self.env['attendance.device.user']

        check_statuses = self.attendance_device_state_line_ids.mapped('code')

        attendances = self.getAttendance()  # Attendance(user_id, timestamp, status)
        for att in attendances:
            if att.punch not in check_statuses:
                continue
            user = User.search([('user_id', '=', att.user_id), ('device_id', '=', self.id), '|', ('active', '=', True), ('active', '=', False)], limit=1)
            utc_dt = self.convert_time_to_utc(att.timestamp, self.tz)
            match = UserAttendance.search([('device_id', '=', self.id),
                                           ('user_id', '=', user.id),
                                           ('status', '=', att.punch),
                                           ('timestamp', '=', utc_dt)], limit=1)
            if not match:
                return False, att
        return True, False

    @api.multi
    def action_attendance_clear(self):
        """
        Method to clear all attendance data from the device
        """

        for r in self:
            error_msg = ""
            attendance_clear_safe, att = r.is_attendance_clear_safe()
            if attendance_clear_safe:
                r.clearAttendance()
            else:
                error_msg += _("It was not safe to clear attendance data from the device %s.<br />") % (r.name,)
                error_msg += _("The following attendance data has not been stored in Odoo yet:<br />")
                error_msg += _("user_id: %s<br />timestamp: %s<br />status: %s<br />") % (att.user_id, att.timestamp, att.punch)
                _logger.warning("It was not safe to clear attendance data from the device %s" % r.name)
                if r.auto_clear_attendance_error_notif:
                    email_template_id = self.env.ref('to_attendance_device.email_template_not_safe_to_clear_attendance')
                    r.post_message(email_template_id)
            if error_msg and r.debug_message:
                r.message_post(body=error_msg)

    @api.multi
    def action_check_connection(self):
        self.ensure_one()
        if self.connect():
            self.disconnect()
            raise UserError(_('Connect to the device %s successfully') % (self.display_name,))

    @api.multi
    def action_device_information(self):
        for r in self:
            r.firmware_version = r.getFirmwareVersion()
            r.serialnumber = r.getSerialNumber()
            r.platform = r.getPlatform()
            r.oem_vendor = r.getOEMVendor()
            r.fingerprint_algorithm = r.getFingerprintAlgorithm()
            r.device_name = r.getDeviceName()
            r.work_code = r.getWorkCode()

    @api.model
    def post_message(self, email_template):
        if self.user_id:
            self.message_subscribe([self.user_id.partner_id.id])
        if email_template:
            self.message_post_with_template(email_template.id)

    @api.multi
    def action_view_users(self):
        action = self.env.ref('to_attendance_device.device_user_list_action')
        result = action.read()[0]

        # reset context
        result['context'] = {}

        # choose the view_mode accordingly
        if self.device_users_count != 1:
            result['domain'] = "[('id', 'in', " + str(self.device_user_ids.ids) + ")]"
        elif self.device_users_count == 1:
            res = self.env.ref('to_attendance_device.attendance_device_user_form_view', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = self.device_user_ids.id
        return result

    @api.multi
    def action_view_attendance_data(self):
        self.ensure_one()
        action = self.env.ref('to_attendance_device.action_user_attendance_data')
        result = action.read()[0]

        # reset context
        result['context'] = {}
        # choose the view_mode accordingly
        total_att_records = self.total_att_records
        if total_att_records != 1:
            result['domain'] = "[('device_id', 'in', " + str(self.ids) + ")]"
        elif total_att_records == 1:
            res = self.env.ref('to_attendance_device.view_attendance_data_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = self.user_attendance_ids.id
        return result

    @api.multi
    def action_view_mapped_employees(self):
        action = self.env.ref('hr.open_view_employee_list_my')
        result = action.read()[0]

        # reset context
        result['context'] = {}
        # choose the view_mode accordingly
        if self.mapped_employees_count != 1:
            result['domain'] = "[('id', 'in', " + str(self.mapped_employee_ids.ids) + ")]"
        elif self.mapped_employees_count == 1:
            res = self.env.ref('to_attendance_device.view_employee_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = self.mapped_employee_ids.id
        return result

    @api.multi
    def action_view_finger_template(self):
        self.ensure_one()
        action = self.env.ref('to_attendance_device.action_finger_template')
        result = action.read()[0]

        # reset context
        result['context'] = {}
        # choose the view_mode accordingly
        total_finger_template_records = self.total_finger_template_records
        if total_finger_template_records != 1:
            result['domain'] = "[('device_id', 'in', " + str(self.ids) + ")]"
        elif total_finger_template_records == 1:
            res = self.env.ref('to_attendance_device.view_finger_template_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = self.finger_templates_ids.id
        return result

    @api.multi
    def unlink(self):
        force_delete = self.env.context.get('force_delete', False)
        for r in self:
            if r.state != 'draft':
                raise UserError(_("You cannot delete the device '%s' while its state is not Draft.")
                                % (r.display_name,))
            if r.device_user_ids and not force_delete:
                raise UserError(_("You may not be able to delete the device '%s' while its data is stored in Odoo."
                                  " Please remove all the related data of this device before removing it from Odoo."
                                  " You may also consider to deactivate this device so that you don't have to delete"
                                  " it.") % (r.display_name,))
        return super(AttendanceDevice, self).unlink()


class AttendanceDeviceStateLine(models.Model):
    _name = 'attendance.device.state.line'
    _description = 'Attendance Device State'

    attendance_state_id = fields.Many2one('attendance.state', string='State Code', required=True, index=True,)
    device_id = fields.Many2one('attendance.device', string='Device', required=True, ondelete='cascade', index=True, copy=False)
    code = fields.Integer(string='Code Number', related='attendance_state_id.code', store=True, readonly=True)
    type = fields.Selection([('checkin', 'Check-in'),
                            ('checkout', 'Check-out')], related='attendance_state_id.type',
                            store=True, readonly=True, index=True)
    activity_id = fields.Many2one('attendance.activity', related='attendance_state_id.activity_id',
                                  help='Attendance activity, e.g. Normal Working, Overtime, etc', readonly=True, store=True, index=True)

    _sql_constraints = [
        ('attendance_state_id_device_id_unique',
         'UNIQUE(attendance_state_id, device_id)',
         "The Code must be unique per Device"),
    ]

    @api.onchange('attendance_state_id')
    def onchange_attendance_state_id(self):
        self.type = self.attendance_state_id.type

