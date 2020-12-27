from odoo import models, SUPERUSER_ID


class IrUiView(models.Model):
    _inherit = 'ir.ui.view'

    def _apply_group(self, model, node, modifiers, fields):
        result = super(IrUiView, self)._apply_group(model, node, modifiers, fields)
        # Rules not work for superuser
        if not result or self._uid == SUPERUSER_ID:
            return result
        try:
            self._cr.execute("SELECT id FROM ir_model WHERE model=%s", (model,))
            model_rec = self.env['ir.model'].sudo().browse(self._cr.fetchone()[0])
            for config_rec in model_rec.field_configuration_ids:
                if (node.tag == 'field' and node.get('name') == config_rec.field_id.name):
                    print("self.env.user.groups_id : ", self.env.user.groups_id)
                    print("config_rec.group_ids : ", config_rec.group_ids)
                    if self.env.user.groups_id & config_rec.group_ids:
                        if config_rec.invisible:
                            modifiers['invisible'] = config_rec.invisible
                            node.set('invisible', '1')
                        if config_rec.readonly:
                            modifiers['readonly'] = config_rec.readonly
                            node.set('readonly', '1')
        except Exception:
            return True
        return True
