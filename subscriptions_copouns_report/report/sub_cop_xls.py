# -*- coding: utf-8 -*-
from odoo.http import request
from odoo import models, api, fields
from datetime import date, datetime
from odoo.exceptions import UserError, ValidationError

from datetime import datetime, timedelta


class SubCopReportXls(models.AbstractModel):
    _name = 'report.subscriptions_copouns_report.sub_cop_report_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, lines):
        name = data['form']

        if name['type'] == 'subscription':
            worksheet = workbook.add_worksheet("Subscription Report")
        else:
            worksheet = workbook.add_worksheet("Coupon Report")

        worksheet.right_to_left()

        cell_text_format = workbook.add_format({'align': 'center',
                                                'bold': True, 'bg_color': '#acb0b0',
                                                'size': 12, 'border': True})
        cell_text_format1 = workbook.add_format({'align': 'center',
                                                 'bold': True,
                                                 'size': 12, 'border': True})
        cell_text_format_values = workbook.add_format({'align': 'center',
                                                       'bold': False,
                                                       'size': 10, 'border': True})
        worksheet.set_column('A:Q', 20)
        row, col = 0, 0

        worksheet.write(row + 2, col, 'تاريخ من', cell_text_format)
        worksheet.write(row + 2, col + 1, str(name['start_date']), cell_text_format1)
        worksheet.write(row + 2, col + 2, 'تاريخ الى', cell_text_format)
        worksheet.write(row + 2, col + 3, str(name['end_date']), cell_text_format1)

        if name['type'] == 'subscription':
            subscriptions = self.env['sale.subscription'].search([('date_start', '>=', name['start_date']),
                                                                  ('date', '<=', name['end_date']),
                                                                  ('subs_products_ids', '!=', None)])
            for sub in subscriptions:
                row += 1
                worksheet.write(row + 4, col, 'رقم الإشتراك', cell_text_format)
                worksheet.write(row + 4, col + 1, 'نوع الإشتراك', cell_text_format)
                worksheet.write(row + 4, col + 2, 'اسم العميل', cell_text_format)
                worksheet.write(row + 4, col + 3, 'تاريخ البدايه', cell_text_format)
                worksheet.write(row + 4, col + 4, 'تاريخ النهاية', cell_text_format)
                worksheet.write(row + 4, col + 5, 'حالة الإشتراك', cell_text_format)
                # Add values
                worksheet.write(row + 5, col, sub.code, cell_text_format_values)
                worksheet.write(row + 5, col + 1, sub.template_id.name, cell_text_format_values)
                worksheet.write(row + 5, col + 2, sub.partner_id.name, cell_text_format_values)
                worksheet.write(row + 5, col + 3, str(sub.date_start), cell_text_format_values)
                worksheet.write(row + 5, col + 4, str(sub.date), cell_text_format_values)
                worksheet.write(row + 5, col + 5, sub.stage_id.name, cell_text_format_values)
                for line in sub.subs_products_ids:
                    row += 1
                    worksheet.merge_range(row + 6, col + 1, row + 6, col + 3, 'نوع السيارة', cell_text_format)
                    worksheet.write(row + 6, col + 4, 'الكمية الإجمالية المستحقه', cell_text_format)
                    worksheet.write(row + 6, col + 5, 'الكمية المستخدمة حتى اليوم', cell_text_format)
                    worksheet.write(row + 6, col + 6, 'الكمية المستحقة حتى اليوم', cell_text_format)
                    worksheet.write(row + 6, col + 7, 'قيمة الإشتراك', cell_text_format)
                    worksheet.write(row + 6, col + 8, 'إجمالي تكلفة الإستخدام', cell_text_format)
                    worksheet.write(row + 6, col + 9, 'هامش الربح', cell_text_format)
                    worksheet.write(row + 6, col + 10, 'نسبة الإستخدام', cell_text_format)
                    # Add values
                    worksheet.merge_range(row + 7, col + 1, row + 7, col + 3, line.vehicle_id.name,
                                          cell_text_format_values)
                    worksheet.write(row + 7, col + 4, line.qty, cell_text_format_values)
                    worksheet.write(row + 7, col + 5, line.consumed_qty, cell_text_format_values)
                    worksheet.write(row + 7, col + 6, (line.qty - line.consumed_qty), cell_text_format_values)
                    worksheet.write(row + 7, col + 7, '', cell_text_format_values)
                    worksheet.write(row + 7, col + 8, '', cell_text_format_values)
                    worksheet.write(row + 7, col + 9, '', cell_text_format_values)
                    worksheet.write(row + 7, col + 10, '', cell_text_format_values)
                row += 4
        else:
            coupons = self.env['sale.coupon'].search([('start_date_use', '>=', name['start_date']),
                                                      ('start_date_use', '<=', name['end_date'])])

            worksheet.write(row + 4, col, 'رقم الكوبون', cell_text_format)
            worksheet.merge_range(row + 4, col + 1, row + 4, col + 3, 'إسم برنامج الكوبون', cell_text_format)
            worksheet.write(row + 4, col + 4, 'اسم العميل', cell_text_format)
            worksheet.write(row + 4, col + 5, 'نوع السياره', cell_text_format)
            worksheet.write(row + 4, col + 6, 'تاريخ البدايه', cell_text_format)
            worksheet.write(row + 4, col + 7, 'تاريخ النهاية', cell_text_format)
            worksheet.write(row + 4, col + 8, 'الكمية الإجمالية المستحقه', cell_text_format)
            worksheet.write(row + 4, col + 9, 'الكمية المستخدمة حتى اليوم', cell_text_format)
            worksheet.write(row + 4, col + 10, 'قيمة الكوبون', cell_text_format)
            worksheet.write(row + 4, col + 11, 'إجمالي تكلفة الإستخدام', cell_text_format)
            worksheet.write(row + 4, col + 12, 'هامش الربح', cell_text_format)
            worksheet.write(row + 4, col + 13, 'نسبة الإستخدام', cell_text_format)
            worksheet.write(row + 4, col + 14, 'حالة الكوبون', cell_text_format)

            for cop in coupons:
                program = self.env['sale.coupon.program'].search([('id', '=', cop.program_id.id)])
                # Add values
                worksheet.write(row + 5, col, cop.code, cell_text_format_values)
                worksheet.merge_range(row + 5, col + 1, row + 5, col + 3, cop.program_id.name, cell_text_format_values)
                worksheet.write(row + 5, col + 4, cop.partner_id.name if cop.partner_id else '-', cell_text_format_values)
                worksheet.write(row + 5, col + 5, cop.vehicle_id.name if cop.vehicle_id else '-', cell_text_format_values)
                worksheet.write(row + 5, col + 6, str(cop.start_date_use), cell_text_format_values)
                worksheet.write(row + 5, col + 7, str(cop.end_date_use), cell_text_format_values)
                worksheet.write(row + 5, col + 8, '', cell_text_format_values)
                worksheet.write(row + 5, col + 9, '', cell_text_format_values)
                worksheet.write(row + 5, col + 10, '', cell_text_format_values)
                worksheet.write(row + 5, col + 11, '', cell_text_format_values)
                worksheet.write(row + 5, col + 12, '', cell_text_format_values)
                worksheet.write(row + 5, col + 13, '', cell_text_format_values)
                worksheet.write(row + 5, col + 14, cop.state, cell_text_format_values)
                row += 1
