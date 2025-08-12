from odoo import models, _, fields, api
from odoo.exceptions import UserError, ValidationError


class AccountPaymentMethod(models.Model):
	_inherit = ['account.payment.method.line', 'mail.thread', 'mail.activity.mixin']
	_name = 'account.payment.method.line'

	payment_mode = fields.Selection([
		('normal', 'Normal'),
		('installments', 'Installments')
	], string="Payment Mode", tracking=True)

	installment_line_ids = fields.One2many(
		'payment.installments', 'payment_method_id', string="Installment Lines"
	)

	@api.constrains('payment_mode', 'installment_line_ids')
	def _check_installments_required(self):
		for rec in self:
			if rec.payment_mode == 'installments' and not rec.installment_line_ids:
				raise ValidationError(_("At least one installment line is required when payment mode is Installments."))

class PaymentInstallments(models.Model):
	_name = 'payment.installments'
	_description = 'Payment Installments'

	name = fields.Char(string="Name", required=True)
	installment_no = fields.Integer(string="Installment No", required=True)
	user_max_discount = fields.Float(string="User Max Discount")
	manager_max_discount = fields.Float(string="Manager Max Discount")
	payment_method_id = fields.Many2one('account.payment.method.line', string="Payment Method")

	@api.constrains('name')
	def _check_name_required(self):
		for rec in self:
			if not rec.name:
				raise ValidationError("Required Installment lines.")