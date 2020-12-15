import time
from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import UserError

class RenewProductWarranty(models.TransientModel):
    _name = 'renew.product.warranty'
    _description = "Renew Product Warranty"

    name = fields.Char("Name", required=True, help="Product Warranty Name ")

    sale_order_id = fields.Many2one("sale.order", string="Sale Order", help="Create Warranty Using  Selected Order.",
                                    copy=False)
    sale_order_line_id = fields.Many2one("sale.order.line", string="Sale Order Line",
                                         help="Create Warranty Using Selected Order Line.",
                                         copy=False)
    partner_id = fields.Many2one("res.partner", string="Customer")

    sale_product_id = fields.Many2one("product.product", string="Product")

    warranty_type_id = fields.Many2one("product.warranty.type", "Warranty Type")

    warranty_start_date = fields.Date("Warranty Start Date")

    warranty_end_date = fields.Date("Warranty End Date")
    warranty_product_id = fields.Many2one("product.product", "Warranty Product")
    no_of_renew = fields.Integer("No. Of Renew")

    note = fields.Html("Note", help="Notes related to this warranty.")

    active = fields.Boolean('Active', default=True, help="Check / uncheck to make warranty record active / inacive.")

    state = fields.Selection([('Running', 'Running'),
                              ('To_Be_Expire', 'To Be Expire'),
                              ('Renewed', 'Renewed'),
                              ('Expired', 'Expired')], string="Status", default="Running")
    product_uom_qty = fields.Integer(string="Ordered Qty")
    parent_warranty_id = fields.Many2one("product.warranty.management", string="Warranty", help="Related Warranty ")

    @api.model
    def default_get(self,  default_fields):
        res = super(RenewProductWarranty, self).default_get(default_fields)
        warranty_id = self.env['product.warranty.management'].browse(self._context.get('active_ids',[]))
        if warranty_id:
            res.update({'sale_order_id':warranty_id.sale_order_id and warranty_id.sale_order_id.id,
                    'name':"Renew_%s"%(warranty_id.name),
                    'sale_order_line_id':warranty_id.sale_order_line_id and warranty_id.sale_order_line_id.id,
                    'partner_id':warranty_id.partner_id and warranty_id.partner_id.id,
                    'sale_product_id':warranty_id.sale_product_id and warranty_id.sale_product_id.id,
                    'warranty_type_id':warranty_id.warranty_type_id and warranty_id.warranty_type_id.id,
                    'warranty_start_date':warranty_id.warranty_start_date,
                    'warranty_end_date':warranty_id.calculate_end_date(warranty_id.warranty_type_id and warranty_id.warranty_type_id),
                    'warranty_product_id':warranty_id.warranty_product_id and warranty_id.warranty_product_id.id,
                    'product_uom_qty':warranty_id.product_uom_qty,
                    'parent_warranty_id':warranty_id.id
                    })
        return res

    
    def renew_product_warranty(self):
        warranty_obj = self.env['product.warranty.management']
        warranty_id=warranty_obj.create({'name': self.name,
                             'sale_order_id': self.sale_order_id and self.sale_order_id.id,
                             'partner_id': self.partner_id and self.partner_id.id,
                             'sale_product_id': self.sale_product_id and self.sale_product_id.id,
                             'warranty_type_id': self.warranty_type_id and self.warranty_type_id.id,
                             'warranty_product_id': self.warranty_product_id and self.warranty_product_id.id,
                             'state': 'Running',
                             'sale_order_line_id': self.sale_order_line_id and self.sale_order_line_id.id,
                             'product_uom_qty': self.product_uom_qty,
                             'warranty_start_date': self.warranty_start_date,
                             'warranty_end_date': self.warranty_end_date,
                             'parent_warranty_id':self.parent_warranty_id and self.parent_warranty_id.id})
        if warranty_id.parent_warranty_id:
            warranty_id.parent_warranty_id.state="Renewed"
            warranty_id.parent_warranty_id.no_of_renew=1