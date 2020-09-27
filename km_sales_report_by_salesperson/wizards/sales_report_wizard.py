from odoo import models, fields, api, _

class SalesReportBySalesperson(models.TransientModel):
    _name = 'sale.salesperson.report'

    start_date = fields.Datetime(string="Start Date", required=True)
    end_date = fields.Datetime(string="End Date", required=True)
    salesperson_ids = fields.Many2many('res.users', string="Salesperson", required=True)

    def print_sale_report_by_salesperson(self):
        sales_order = self.env['sale.order'].search([])
        sale_order_groupby_dict = {}
        for salesperson in self.salesperson_ids:
            filtered_sale_order = list(filter(lambda x: x.user_id == salesperson, sales_order))
            print('filtered_sale_order ===',filtered_sale_order)
            filtered_by_date = list(filter(lambda x: x.date_order >= self.start_date and x.date_order <= self.end_date, filtered_sale_order))
            sale_order_groupby_dict[salesperson.name] = filtered_by_date

        final_dist = {}
        for salesperson in sale_order_groupby_dict.keys():
            sale_data = []
            for order in sale_order_groupby_dict[salesperson]:
                temp_data = []
                temp_data.append(order.name)
                temp_data.append(order.date_order)
                temp_data.append(order.partner_id.name)
                temp_data.append(order.amount_total)
                sale_data.append(temp_data)
            final_dist[salesperson] = sale_data
        datas = {
            'ids': self,
            'model': 'sale.salesperson.report',
            'form': final_dist,
            'start_date': self.start_date,
            'end_date': self.end_date
        }
        return self.env.ref('km_sales_report_by_salesperson.action_report_by_salesperson').report_action([], data=datas)