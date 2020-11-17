from odoo import models, fields

class FleetVehicle(models.Model):
	_inherit = 'fleet.vehicle'
	_description = 'Vehicle'
	
	color = fields.Many2one('fleet.color',string='color')
	model_year = fields.Many2one('fleet.model',string='Model Year', help='Year of the model')


class FleetColor(models.Model):
	_name = 'fleet.color'
	_description = 'Vehicle Color'
	name = fields.Char('Color ')

class FleetModel(models.Model):
	_name = 'fleet.model'
	_description = 'Vehicle Model Addon'

	name = fields.Char('Model')

