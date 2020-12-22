from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    ir_cron_scheduler_sync_attendance = env.ref('to_attendance_device.ir_cron_scheduler_sync_attendance', raise_if_not_found=False)
    if ir_cron_scheduler_sync_attendance:
        ir_cron_scheduler_sync_attendance.write({
            'function': 'cron_sync_attendance'
            })
