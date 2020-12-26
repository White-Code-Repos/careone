from odoo import models, fields, api, tools, _

class HrAttendancePolicy(models.Model):
	_inherit = 'hr.attendance.policy'
	def get_overtime(self):
		self.ensure_one()
		res = {}
		if self:
			overtime_ids = self.overtime_rule_ids
			wd_ot_id = self.overtime_rule_ids.search([('type', '=', 'workday'), ('id', 'in', overtime_ids.ids)],order='id', limit=0)
			we_ot_id = self.overtime_rule_ids.search([('type', '=', 'weekend'), ('id', 'in', overtime_ids.ids)],order='id', limit=0)
			ph_ot_id = self.overtime_rule_ids.search([('type', '=', 'ph'), ('id', 'in', overtime_ids.ids)],order='id', limit=0)
			if wd_ot_id:
				res['wd_rate'] = wd_ot_id.rate
				res['wd_after'] = wd_ot_id.active_after
				res['wd_3h'] = wd_ot_id.up_to_3h_rate
				res['wd_after_3h'] = wd_ot_id.over_3h_rate
			else:
				res['wd_rate'] = 0
				res['wd_after'] = -1
				res['wd_3h'] = 1
				res['wd_after_3h'] = 1
			if we_ot_id:
				res['we_rate'] = we_ot_id.rate
				res['we_after'] = we_ot_id.active_after
			else:
				res['we_rate'] = 0
				res['we_after'] = -1
			if ph_ot_id:
				res['ph_rate'] = ph_ot_id.rate
				res['ph_after'] = ph_ot_id.active_after
			else:
				res['ph_rate'] = 0
				res['ph_after'] = -1
		else:
			res['wd_rate'] = res['wd_rate'] = res['ph_rate'] = 0
			res['wd_after'] = res['we_after'] = res['ph_after'] = -1
		return res
