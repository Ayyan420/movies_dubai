from odoo import models, fields, api
from datetime import date, timedelta


class AccountMove(models.Model):
	_inherit = 'account.move'

	payment_method_id = fields.Many2one(
		'account.payment.method',
		string='Payment Method',
		tracking=True
	)
	target_delivery_date = fields.Date(string="Target Delivery Date",tracking=True)

	@api.model
	def create(self, vals):
		if vals.get('invoice_origin'):
			sale = self.env['sale.order'].search([('name', '=', vals['invoice_origin'])], limit=1)
			if sale:
				vals['payment_method_id'] = sale.payment_method_id.id if sale.payment_method_id else False
				vals['target_delivery_date'] = sale.target_delivery_date
		return super().create(vals)


class AccountMoveLine(models.Model):
	_inherit = 'account.move.line'

	custom_description = fields.Char(string="Custom Description")