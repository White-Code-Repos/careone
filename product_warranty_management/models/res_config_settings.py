from odoo import api,fields, models
class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    warranty_expire_duration = fields.Integer(string="Alert Warranty Expire Duration",
                                              help="If Warranty Will be expire with in a time duration, Before time duration we will alert using state",default=1)

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        res.update( warranty_expire_duration =  int(params.get_param('product_warranty_management.warranty_expire_duration', default=1)))
        return res


    
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        ICPSudo.set_param("product_warranty_management.warranty_expire_duration", self.warranty_expire_duration)
