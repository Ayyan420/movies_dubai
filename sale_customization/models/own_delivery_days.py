from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class OwnDeliveryDays(models.Model):
	_name = 'own.delivery.days'
	_description = 'Own Delivery Days'
	_order = 'from_date'
	_check_company_auto = True
	_rec_name='days'
	_inherit = ['mail.thread', 'mail.activity.mixin']

	from_date = fields.Date(string="From Duration", required=True, tracking=True)
	to_date = fields.Date(string="To Duration", required=True, tracking=True)
	days = fields.Integer(string="Delivery Days", required=True, tracking=True)
	company_id = fields.Many2one(
		'res.company', 
		string="Company", 
		default=lambda self: self.env.company, 
		required=True
	)

	@api.constrains('from_date', 'to_date')
	def _check_dates(self):
		for rec in self:
			if rec.from_date > rec.to_date:
				raise ValidationError(_("From Date must be before To Date."))

	@api.constrains('company_id', 'from_date', 'to_date')
	def _check_overlap(self):
		for rec in self:
			overlapping = self.search([
				('id', '!=', rec.id),
				('company_id', '=', rec.company_id.id),
				('from_date', '<=', rec.to_date),
				('to_date', '>=', rec.from_date),
			])
			if overlapping:
				raise ValidationError(_("There is already a record overlapping this date range for the same company."))