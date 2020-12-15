from odoo import fields, models, api,_
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError, Warning


class ProductWarrantyProcess(models.Model):
    _name = "product.warranty.process"
    _rec_name = "sale_order_id"

    sale_order_id = fields.Many2one("sale.order", "Sale Order")
    partner_id = fields.Many2one("res.partner", "Partner")
    warranty_line_ids = fields.One2many('product.warranty.process.line', 'process_id', string='Order Lines')

    
    def calculate_end_date(self, warranty_type_id=False):
        if warranty_type_id.warranty_period_unit == 'Days':
            warranty_end_date = datetime.today() + relativedelta(days=warranty_type_id.warranty_period)
        elif warranty_type_id.warranty_period_unit == 'Weeks':
            warranty_end_date = datetime.today() + relativedelta(
                weeks=warranty_type_id.warranty_period)
        elif warranty_type_id.warranty_period_unit == 'Months':
            warranty_end_date = datetime.today() + relativedelta(
                months=warranty_type_id.warranty_period)
        elif warranty_type_id.warranty_period_unit == 'Years':
            warranty_end_date = datetime.today() + relativedelta(
                years=warranty_type_id.warranty_period)
        return warranty_end_date

    def create_product_warranty(self):
        warranty_obj = self.env['product.warranty.management']
        for warranty_line in self.warranty_line_ids:
            if not warranty_line.warranty_type_id or not warranty_line.warranty_product_id:
                raise ValidationError("Invalid Order Line! %s " % (
                            warranty_line.sale_line_product_id and warranty_line.sale_line_product_id.name or ""))
            if self.env['product.warranty.management'].search([('sale_order_id','=',self.sale_order_id and self.sale_order_id.id),
                                                            ('sale_product_id','=',warranty_line.sale_line_product_id and warranty_line.sale_line_product_id.id),
                                                            ('sale_order_line_id','=',warranty_line.sale_line_id and warranty_line.sale_line_id.id),
                                                            ('state','=','Running')]):
                raise ValidationError("Warranty Already Exist For This Order Line! %s " % (
                        warranty_line.sale_line_product_id and warranty_line.sale_line_product_id.name or ""))


        for warranty_line in self.warranty_line_ids:
            warranty_obj.create({'name': "%s_%s" % (
            warranty_line.sale_line_product_id and warranty_line.sale_line_product_id.name,
            warranty_line.warranty_type_id and warranty_line.warranty_type_id.name),
                                 'sale_order_id': self.sale_order_id and self.sale_order_id.id,
                                 'partner_id': self.partner_id and self.partner_id.id,
                                 'sale_product_id': warranty_line.sale_line_product_id and warranty_line.sale_line_product_id.id,
                                 'warranty_type_id': warranty_line.warranty_type_id and warranty_line.warranty_type_id.id,
                                 'warranty_product_id': warranty_line.warranty_product_id and warranty_line.warranty_product_id.id,
                                 'no_of_renew': 0,
                                 'state': 'Running',
                                 'sale_order_line_id':warranty_line.sale_line_id and warranty_line.sale_line_id.id,
                                 'product_uom_qty': warranty_line.product_uom_qty,
                                 'warranty_start_date': datetime.today(),
                                 'warranty_end_date': self.calculate_end_date(warranty_line.warranty_type_id)})

        action = {
            'name': _('Warranty Process'),
            'type': 'ir.actions.act_window',
            'res_model': 'product.warranty.management',
            'view_mode': 'tree,form',
            'views': [[self.env.ref('product_warranty_management.view_product_warranty_process_tree_view').id, 'list']],
            'target': 'current',
            'domain': [('sale_order_id', '=', self.sale_order_id and self.sale_order_id.id)],
        }
        return action

    
    @api.onchange('sale_order_id')
    def sale_order_onchange(self):
        order_id = self.sale_order_id
        self.warranty_line_ids = False
        if order_id:
            self.partner_id = order_id.partner_id and order_id.partner_id.id
            product_warranty_process_line = []
            for order_line_id in order_id.order_line:
                product_warranty_process_line.append((0,0,{'sale_line_product_id': order_line_id.product_id and order_line_id.product_id.id,
                                                      'product_uom_qty': order_line_id.product_uom_qty,
                                                      'warranty_type_id': order_line_id.product_id and order_line_id.product_id.warranty_type_id.id,
                                                      'warranty_product_id': order_line_id.warranty_product_id and order_line_id.warranty_product_id.id,
                                                      'sale_line_id': order_line_id.id,
                                                      'warranty_product_id':order_line_id.product_id and order_line_id.product_id.warranty_product_id and order_line_id.product_id.warranty_product_id.id,
                                                      'warranty_type_id':order_line_id.product_id and order_line_id.product_id.warranty_type_id and order_line_id.product_id.warranty_type_id.id
                                                      }))
            self.warranty_line_ids = product_warranty_process_line


class ProductWarrantyProcessLine(models.Model):
    _name = "product.warranty.process.line"

    sale_line_product_id = fields.Many2one("product.product", "Product")

    product_uom_qty = fields.Integer(string="Ordered Qty")

    sale_line_id = fields.Many2one("sale.order.line", "Sale Order Line", copy=False)

    process_id = fields.Many2one("product.warranty.process", "Process", copy=False)

    warranty_type_id = fields.Many2one("product.warranty.type", "Warranty Type", copy=False)

    warranty_product_id = fields.Many2one("product.product", "Warranty Product")
