from odoo import models, fields, api, _
from odoo.exceptions import UserError

class AccountMove(models.Model):
	_inherit = 'account.move'

	user_attachment_ids = fields.Many2many(
		'ir.attachment',
		'account_move_user_attachment_rel',
		'move_id',
		'attachment_id',
		string='Receipt Attachments',
		domain="[('res_model', '=', 'account.move'), ('res_id', '=', id), ('mimetype', '!=', 'application/pdf')]",
		help="Attach only user-uploaded documents, not auto-generated ones.",
		tracking=True
	)

	# def action_register_payment(self):
	# 	for move in self:
	# 		if move.move_type == 'out_invoice':
	# 			if not move.user_attachment_ids:
	# 				raise UserError(_("Please upload at least one payment receipt document before registering the payment."))
	# 			if not move.payment_reference:
	# 				raise UserError(_("Please add payment/transaction reference before registering the payment."))
	# 	return super(AccountMove, self).action_register_payment()

	payment_installment_id = fields.Many2many(
		'payment.installments',
		string='Payment Installment',
		tracking=True
	)

	payment_method_id = fields.Many2many(
		'account.payment.method.line',
		string='Payment Method',
		tracking=True
	)

	target_delivery_date = fields.Date(string="Target Delivery Date",tracking=True)


	payment_method_payment_mode = fields.Selection(
		selection=[
			('normal', 'Normal'),
			('installments', 'Installments')
		],
		string="Payment Mode",
		compute='_compute_payment_method_payment_mode',
		store=True,
		readonly=True,
	)

	@api.depends('payment_method_id.payment_mode')
	def _compute_payment_method_payment_mode(self):
		for rec in self:
			if rec.payment_method_id.filtered(lambda pm: pm.payment_mode == 'installments'):
				rec.payment_method_payment_mode = 'installments'
			elif rec.payment_method_id:
				rec.payment_method_payment_mode = 'normal'
			else:
				rec.payment_method_payment_mode = False

				
	@api.model
	def create(self, vals):
		if vals.get('invoice_origin'):
			sale = self.env['sale.order'].search(
				[('name', '=', vals['invoice_origin'])],
				limit=1
			)
			if sale:
				vals['payment_method_id'] = sale.payment_method_id.ids
				vals['payment_installment_id'] = sale.payment_installment_id.ids
				vals['target_delivery_date'] = sale.target_delivery_date
		return super().create(vals)


class AccountMoveLine(models.Model):
	_inherit = 'account.move.line'
	
	custom_description = fields.Char(string="Custom Description",tracking=True)


class AccountPaymentMethod(models.Model):
	_inherit = 'account.payment.method.line'
	
	user_max_discount = fields.Float(string="User Max Discount (%)", tracking=True)
	manager_max_discount = fields.Float(string="Manager Max Discount (%)", tracking=True)