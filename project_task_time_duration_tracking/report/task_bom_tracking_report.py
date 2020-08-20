# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo import tools


class TaskBomTrackingReport(models.Model):
    _name = "task.bom.tracking.report"
    _description = "Task BOM Tracking Report"
    _auto = False

    task_id = fields.Many2one('project.task', string='Task', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Customer', readonly=True)
    start_date = fields.Datetime(string='Start Date', readonly=True)
    stop_date = fields.Datetime(string='Stop Date', readonly=True)
    product_id = fields.Many2one('product.product', string='Product', readonly=True)
    product_uom_qty = fields.Float(string='Qty', readonly=True)
    planned_hours = fields.Float(string='Duration', readonly=True)
    user_id = fields.Many2one('res.users', string='User', readonly=True)

    @api.model
    def _query(self):
        return '''
            SELECT 
                stb.id,
                stb.task_id as task_id,
                stb.partner_id as partner_id,
                stb.product_id as product_id,
                stb.product_uom_qty as product_uom_qty,
                pt.task_datetime_start as start_date,
                pt.task_datetime_stop as stop_date,
                pt.user_id as user_id,
                pt.planned_hours as planned_hours
            FROM 
                sale_task_bom AS stb,
                project_task AS pt
            WHERE 
                stb.task_id = pt.id
            GROUP BY
                stb.id,
                stb.task_id,
                stb.partner_id,
                stb.product_id,
                stb.product_uom_qty,
                pt.task_datetime_start,
                pt.task_datetime_stop,
                pt.user_id,
                pt.planned_hours
        '''

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute('''
            CREATE OR REPLACE VIEW %s AS (%s)''' % (
            self._table, self._query()
        ))
