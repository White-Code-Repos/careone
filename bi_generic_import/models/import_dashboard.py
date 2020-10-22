from odoo import models, fields, api
from datetime import datetime

class marketplace_inventory(models.Model):
    _name = 'import.dashboard'
    _description = "import Dashboard"

    def _count(self):
        for count in self:
            template_obj = self.env['product.template']
            variant_obj = self.env['product.product']
            pricelist_obj = self.env['product.pricelist']
            purchase_obj = self.env['purchase.order']
            inv_bill_obj = self.env['account.move']
            picking_obj = self.env['stock.picking']
            partner_obj = self.env['res.partner']
            sorder_obj = self.env['sale.order']
            inventory_obj = self.env['stock.inventory']
            payment_obj = self.env['account.payment']
            mrp_obj = self.env['mrp.bom']
            if count.state == 'sale.order':
                import_count = sorder_obj.sudo().search_count([('is_import','=',True)])
                count.import_data = import_count
            elif count.state == 'purchase.order':
                import_count = purchase_obj.sudo().search_count([('is_import','=',True)])
                count.import_data = import_count                
            elif count.state == 'account.move':
                import_count = inv_bill_obj.sudo().search_count([('is_import','=',True)])
                count.import_data = import_count                
            elif count.state == 'stock.picking':
                import_count = picking_obj.sudo().search_count([('is_import','=',True)])
                count.import_data = import_count  
            elif count.state == 'mrp.bom':    
                import_count = mrp_obj.sudo().search_count([('is_import','=',True)])
                count.import_data = import_count                  
            elif count.state == 'res.partner':    
                import_count = partner_obj.sudo().search_count([('is_import','=',True)])
                count.import_data = import_count                  
            elif count.state == 'product.pricelist':  
                import_count = pricelist_obj.sudo().search_count([('is_import','=',True)])
                count.import_data = import_count  
            elif count.state == 'product.template':    
                import_count = template_obj.sudo().search_count([('is_import','=',True)])
                count.import_data = import_count                  
            elif count.state == 'product.product':
                import_count = variant_obj.sudo().search_count([('is_import','=',True)])
                count.import_data = import_count  
            elif count.state == 'stock.inventory':
                import_count = inventory_obj.sudo().search_count([('is_import','=',True)])
                count.import_data = import_count  
            elif count.state == 'account.payment':
                import_count = payment_obj.sudo().search_count([('is_import','=',True)])
                count.import_data = import_count  
            else:
                count.import_data = 0
        return True

    name = fields.Char('Import Dashboard')
    state = fields.Selection([
        ('sale.order', 'Sale Orders'), 
        ('purchase.order', 'Purchase Orders'),
        ('account.move', 'Invoice/Bill'),
        ('stock.picking', 'Picking'),
        ('mrp.bom', 'mrp'),
        ('res.partner', 'Partner'),
        ('product.pricelist', 'Pricelist'),
        ('product.template', 'Product Template'),
        ('product.product', 'Product Variant'),
        ('stock.inventory', 'Inventory'),
        ('account.payment', 'payment'),
        ])
    import_data = fields.Integer('Pending Count',default=0,compute="_count")