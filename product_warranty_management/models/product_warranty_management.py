from odoo import models, fields, api, _
from datetime import datetime,timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError, Warning


class ProductWarrantyManagement(models.Model):
    _name = "product.warranty.management"

    name = fields.Char("Name", required=True, help="Product Warranty Name ")

    sale_order_id = fields.Many2one("sale.order", string="Sale Order",help="Create Warranty Using  Selected Order.",copy=False)
    sale_order_line_id = fields.Many2one("sale.order.line", string="Sale Order Line", help="Create Warranty Using Selected Order Line.",
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
    parent_warranty_id = fields.Many2one("product.warranty.management",string="Warranty",help="Related Warranty ")
    
    child_warranty_ids = fields.One2many("product.warranty.management","parent_warranty_id",string="Warranty",help="Related Warranties")
    child_claim_ids = fields.One2many("product.warranty.claim", "warrenty_id", string="Product Claims")
    warranty_count = fields.Integer(string='Child Warranty', compute='_compute_child_warranty_ids')
    

    @api.depends('child_warranty_ids')
    def _compute_child_warranty_ids(self):
        for warranty in self:
            warranty.warranty_count = len(warranty.child_warranty_ids)

    def actionid_product_warranty_type(self):
        action = {
            'name': _('Warranty Process'),
            'type': 'ir.actions.act_window',
            'res_model': 'product.warranty.management',
            'view_mode': 'tree,form',
            'views': [[self.env.ref('product_warranty_management.view_product_warranty_process_tree_view').id, 'list']],
            'target': 'current',
            'domain': [('sale_order_id', '=', self.sale_order_id and self.sale_order_id.id),('parent_warranty_id', '!=',False)],
        }
        return action

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

    def cron_set_warranty_status(self):
        exipiration_days = int(self.env['ir.config_parameter'].sudo().get_param('product_warranty_management.warranty_expire_duration') or 1)
        expiration_period = fields.Date.today()+timedelta(days=exipiration_days)
        records_to_process = self.search([('state','=','Running'),('warranty_end_date','<=',expiration_period)])
        records_to_process.write({'state':'To_Be_Expire'})
        expired_records = self.search([('state','=','To_Be_Expire'),('warranty_end_date','<=',fields.Date.today())])
        expired_records.write({'state': 'Expired'})
        return True
        
    ######################################
    ####            Send Warranty ########
    ######################################
    def action_quotation_send(self):
        ''' Opens a wizard to compose an email, with relevant mail template loaded by default '''
        self.ensure_one()
        template_id = self._find_mail_template()
        lang = self.env.context.get('lang')
        template = self.env['mail.template'].browse(template_id)
        if template.lang:
            lang = template._render_template(template.lang, 'product.warranty.management', self.ids[0])
        ctx = {
            'default_model': 'product.warranty.management',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True,
            'custom_layout': "mail.mail_notification_paynow",
            'proforma': self.env.context.get('proforma', False),
            'force_email': True,
            #'model_description': self.with_context(lang=lang).type_name,
        }
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }
        
    def _find_mail_template(self, force_confirmation_template=False):
        template_id = False
        #template_id = int(self.env['ir.config_parameter'].sudo().get_param('sale.default_confirmation_template'))
        template_id = self.env['mail.template'].search([('model', '=', 'product.warranty.management')]).id
        return template_id

class ProductWarrantyType(models.Model):
    _name = "product.warranty.type"
    name=fields.Char("Name",required=True,help="Product Warranty Type Name")
    warranty_period = fields.Integer("Warranty Period",required=True, help="Warranty Period in months for this particular warranty type.")
    warranty_period_unit = fields.Selection([('Days','Days'),
                                             ('Weeks','Weeks'),
                                             ('Months','Months'),
                                             ('Years','Years')],
                                            string="Unit",default='Days',help="Warranty Period Unit")
    is_default = fields.Boolean("Is Default")
    note = fields.Html("Note", help="Notes related to this warranty.")
    
class ProductWarrantyClaim(models.Model):
    _name = "product.warranty.claim"

    name = fields.Char("Claim Subject", required=True, help="Claim Subject ")
    date = fields.Date("Claim Date")
    uid = fields.Many2one('res.users',string = "Responsible")
    steam = fields.Many2one('crm.team', string ="Sales Team")
    
    warrenty_id = fields.Many2one("product.warranty.management", string="Sale Warranty")
    dead_line = fields.Date("Dead Line")
    
    
    partner_id = fields.Many2one("res.partner", string="Customer")

    phone = fields.Char("Phone")
    email=fields.Char("email")
    product_id = fields.Many2one("product.product",string = "Product / Service ")
    serial_no = fields.Char("Serial No.")

    note = fields.Html("Claim Description", help="Notes related to this warranty.")

    active = fields.Boolean('Active', default=True, help="Check / uncheck to make warranty record active / inacive.")

    state = fields.Selection([('new', 'New'),
                              ('under_maintenance', 'Under Maintenance'),
                              ('ready_to_deliver', 'Ready To Deliver'),
                              ('done', 'Done')], string="Status", default="new")