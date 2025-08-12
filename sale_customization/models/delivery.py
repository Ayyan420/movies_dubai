from odoo import _, api, fields, models
from odoo.exceptions import UserError

class ChooseDeliveryCarrier(models.TransientModel):
	_inherit = 'choose.delivery.carrier'

	own_delivery_price = fields.Float(string="Shipping Cost")

	@api.onchange('delivery_price')
	def _onchange_carrier_id_delivery(self):
		for x in self:
			x.own_delivery_price = x.delivery_price

	@api.onchange('own_delivery_price')
	def _onchange_carrier_id_own(self):
		for x in self:
			if x.own_delivery_price:
				x.delivery_price = x.own_delivery_price