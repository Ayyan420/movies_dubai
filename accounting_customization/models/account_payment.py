import markupsafe
from odoo import Command, models, fields, api, _


class AccountPaymentRegisterInv(models.TransientModel):
	_inherit = 'account.payment.register'

	is_from_sale = fields.Boolean(
		string="From Sale",
		compute="_compute_is_from_sale",
		store=False
	)

	payment_installment_id = fields.Many2many(
		'payment.installments',
		string='Payment Installment',
		tracking=True,
		compute="_compute_invoice_payment_fields_sale",
		store=False
	)
	
	selected_payment_installment_id= fields.Many2one(
		'payment.installments',
		string='Payment Installment',
		tracking=True,
	)

	payment_method_id = fields.Many2many(
		'account.payment.method.line',
		string='Payment Method',
		tracking=True,
		compute="_compute_invoice_payment_fields_sale",
		store=False
	)

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

	@api.depends('line_ids')
	def _compute_is_from_sale(self):
		SaleOrder = self.env['sale.order']
		for wizard in self:
			from_sale = False
			for line in wizard.line_ids:
				if any(sl.order_id for sl in line.sale_line_ids):
					from_sale = True
					break
				if line.move_id.invoice_origin and SaleOrder.search_count([('name', '=', line.move_id.invoice_origin)]):
					from_sale = True
					break
			wizard.is_from_sale = from_sale

	@api.depends('line_ids')
	def _compute_invoice_payment_fields_sale(self):
		for wizard in self:
			invoices = wizard.line_ids.mapped('move_id')
			wizard.payment_installment_id = invoices.mapped('payment_installment_id')
			wizard.payment_method_id = invoices.mapped('payment_method_id')

	@api.onchange('payment_method_line_id')
	def _onchange_payment_method_line_id_sale(self):
		if self.payment_method_line_id:
			method_line = self.payment_method_line_id[0]
			if method_line.journal_id:
				if not self.journal_id:
					self.journal_id = method_line.journal_id.id
				elif self.journal_id.id != method_line.journal_id.id:
					self.journal_id = method_line.journal_id.id

	@api.onchange('selected_payment_installment_id')
	def _onchange_selected_installments(self):
		if self.selected_payment_installment_id:
			invoices_total = sum(self.line_ids.mapped('amount_residual'))
			num_installments = self.selected_payment_installment_id.installment_no or len(self.selected_payment_installment_id)
			if num_installments > 0:
				split_amount = invoices_total / num_installments
				self.amount = split_amount


	@api.depends('installments_mode')
	def _compute_installments_switch_values(self):
		for wizard in self:
			if not wizard.journal_id or not wizard.currency_id or wizard.selected_payment_installment_id:
				wizard.installments_switch_amount = wizard.installments_switch_amount
				wizard.installments_switch_html = wizard.installments_switch_html
			else:
				total_amount_values = wizard._get_total_amounts_to_pay(wizard.batches)
				html_lines = []
				if wizard.installments_mode == 'full':
					if (
						wizard.currency_id.is_zero(total_amount_values['full_amount'] - wizard.amount)
						and wizard.currency_id.is_zero(total_amount_values['full_amount'] - total_amount_values['amount_by_default'])
					):
						wizard.installments_switch_amount = 0.0
					else:
						wizard.installments_switch_amount = total_amount_values['amount_by_default']
						html_lines += [
							_("This is the full amount."),
							_("Consider paying in %(btn_start)sinstallments%(btn_end)s instead."),
						]
				elif wizard.installments_mode == 'overdue':
					wizard.installments_switch_amount = total_amount_values['full_amount']
					html_lines += [
						_("This is the overdue amount."),
						_("Consider paying the %(btn_start)sfull amount%(btn_end)s."),
					]
				elif wizard.installments_mode == 'before_date':
					wizard.installments_switch_amount = total_amount_values['full_amount']
					next_payment_date = self._get_next_payment_date_in_context()
					html_lines += [
						_("Total for the installments before %(date)s.", date=(next_payment_date or fields.Date.context_today(self))),
						_("Consider paying the %(btn_start)sfull amount%(btn_end)s."),
					]
				elif wizard.installments_mode == 'next':
					wizard.installments_switch_amount = total_amount_values['full_amount']
					html_lines += [
						_("This is the next unreconciled installment."),
						_("Consider paying the %(btn_start)sfull amount%(btn_end)s."),
					]
				else:
					wizard.installments_switch_amount = wizard.installments_switch_amount

				if wizard.custom_user_amount:
					wizard.installments_switch_html = None
				else:
					wizard.installments_switch_html = markupsafe.Markup('<br/>').join(html_lines) % {
						'btn_start': markupsafe.Markup('<span class="installments_switch_button btn btn-link p-0 align-baseline">'),
						'btn_end': markupsafe.Markup('</span>'),
					}