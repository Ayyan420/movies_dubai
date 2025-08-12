from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import date, timedelta


class SaleOrder(models.Model):
	_inherit = 'sale.order'

	max_discount = fields.Float(
		string="Max Allowed Discount",
		store=True,
		tracking=True,
		copy=False
	)

	target_delivery_date = fields.Date(
		string="Target Delivery Date",
		default=lambda self: fields.Date.today(),
		tracking=True,
		copy=False
	)

	payment_method_id = fields.Many2many(
		'account.payment.method.line',
		string='Payment Method',
		tracking=True,
		copy=False
	)

	payment_installment_id = fields.Many2many(
		'payment.installments',
		string='Payment Installment',
		tracking=True,
		copy=False
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
		copy=False
	)

	is_signed = fields.Boolean(string="Is Signed", tracking=True, copy=False)

	def check_the_discount(self):
		for order in self:
			max_discount = order.max_discount or 0.0
			user = self.env.user
			bypass_limit = user.has_group('sales_team.group_sale_manager')

			def get_discount_percentage(order):
				normal_lines = order.order_line.filtered(
					lambda l: l.price_unit > 0 and not getattr(l.product_id, 'is_discount', False)
				)
				total_before = sum(l.price_unit * l.product_uom_qty for l in normal_lines)
				total_after = sum(
					l.price_unit * l.product_uom_qty * (1 - (l.discount or 0.0) / 100.0)
					for l in normal_lines
				)
				discount_lines_total = sum(l.price_unit*l.product_uom_qty for l in order.order_line if l.price_unit < 0)
				total_after += discount_lines_total
				if total_before <= 0:
					return 0
				return ((total_before - total_after) / total_before) * 100
			current_pct = round(get_discount_percentage(order),2)
			new_total_pct = current_pct
			if not bypass_limit and new_total_pct > max_discount:
				raise ValidationError(
					_(f"Total discount {new_total_pct:.2f}% exceeds the allowed maximum of {max_discount}%.")
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

	@api.onchange('payment_method_id', 'payment_installment_id')
	def _onchange_payment_fields(self):
		user = self.env.user
		if user.has_group('sales_team.group_sale_manager'):
			self.max_discount = 100
			return
		if self.payment_method_id:
			if any(pm.payment_mode == 'installments' for pm in self.payment_method_id) and self.payment_installment_id:
				if user.has_group('sales_team.group_sale_salesman_all_leads'):
					self.max_discount = max(self.payment_installment_id.mapped('manager_max_discount') or [0.0])
				else:
					self.max_discount = max(self.payment_installment_id.mapped('user_max_discount') or [0.0])
			else:
				if user.has_group('sales_team.group_sale_salesman_all_leads'):
					self.max_discount = max(self.payment_method_id.mapped('manager_max_discount') or [0.0])
				else:
					self.max_discount = max(self.payment_method_id.mapped('user_max_discount') or [0.0])
		else:
			self.max_discount = 0.0


	def write(self, vals):
		res = super().write(vals)
		if 'payment_method_id' in vals or 'payment_installment_id' in vals:
			for order in self:
				order._onchange_payment_fields()
		if 'signature' in vals and vals['signature']:
			for order in self:
				if order.signature:
					order.is_signed = True
					order._attach_sign()
		return res


	def _attach_sign(self):
		self.ensure_one()
		report = self.env['ir.actions.report']._render_qweb_pdf("sale.action_report_saleorder", self.id)
		filename = f"{self.name}_signed_sale_order.pdf"
		message = _('Order signed by %s', self.partner_id.name) if self.partner_id else _('Order signed')
		self.message_post(
			attachments=[(filename, report[0])],
			body=message,
		)
		return True

	def _action_confirm(self):
		for order in self:
			if not order.is_signed:
				raise UserError(_("Please sign the order first."))
			if not order.carrier_id:
				raise UserError(_("Please Add a shipping Method before confirming the quotation."))
			if not order.payment_method_id:
				raise UserError(_("Please Add a Payment Method before confirming the quotation."))
			if not order.order_line.filtered(lambda line: line.is_delivery):
				raise UserError(_("Please add a delivery line using the shipping wizard before confirming."))
			order.check_the_discount()
			for line in order.order_line:
				line._check_discontinued_stock()
		return super(SaleOrder, self)._action_confirm()

	@api.onchange('order_line')
	def _compute_target_delivery_date(self):
		today = fields.Date.today()
		company = self.company_id or self.env.company
		own_days = self.env['own.delivery.days'].search([
			('company_id', '=', company.id),
			('from_date', '<=', today),
			('to_date', '>=', today)
		], limit=1)
		max_delay = 0
		if own_days:
			max_delay = own_days.days
		for line in self.order_line:
			product = line.product_id
			required_qty = line.product_uom_qty
			if not product.is_storable:
				continue
			warehouse = line.order_id.warehouse_id or self.env['stock.warehouse'].search([('company_id','=',company.id)], limit=1)
			if warehouse:
				free_qty = product.with_context(warehouse_id=warehouse.id).free_qty
				if required_qty > free_qty:
					if product.seller_ids:
						delays = [seller.delay for seller in product.seller_ids if seller.delay]
						if delays:
							product_max_delay = max(delays)
							max_delay += product_max_delay
		self.target_delivery_date = today + timedelta(days=max_delay)

class SaleOrderLine(models.Model):
	_inherit = 'sale.order.line'

	
	@api.onchange('discount','product_uom_qty','product_id','price_unit')
	def check_the_discount_lines(self):
		for line in self:
			max_discount = line.order_id.max_discount or 0.0
			user = self.env.user
			bypass_limit = user.has_group('sales_team.group_sale_manager')

			def get_discount_percentage(order):
				normal_lines = order.order_line.filtered(
					lambda l: l.price_unit > 0 and not getattr(l.product_id, 'is_discount', False)
				)
				total_before = sum(l.price_unit * l.product_uom_qty for l in normal_lines)
				total_after = sum(
					l.price_unit * l.product_uom_qty * (1 - (l.discount or 0.0) / 100.0)
					for l in normal_lines
				)
				discount_lines_total = sum(l.price_unit*l.product_uom_qty for l in order.order_line if l.price_unit < 0)
				total_after += discount_lines_total
				if total_before <= 0:
					return 0
				return ((total_before - total_after) / total_before) * 100
			current_pct = round(get_discount_percentage(line.order_id),2)
			new_total_pct = current_pct
			if not bypass_limit and new_total_pct > max_discount:
				raise ValidationError(
					_(f"Total discount {new_total_pct:.2f}% exceeds the allowed maximum of {max_discount}%.")
				)

	product_default_code = fields.Char(
		string="Reference Code",
		related='product_id.default_code',
		store=True
	)

	custom_description = fields.Text(string='Name/Description',copy=False)

	@api.onchange('product_id')
	def _onchange_product_id_set_description(self):
		if self.product_id:
			self.custom_description = self.name

	@api.onchange('custom_description')
	def _onchange_product_id_set_description_reverse(self):
		if self.product_id:
			self.name = self.custom_description

	def _prepare_invoice_line(self, **optional_values):
		res = super()._prepare_invoice_line(**optional_values)
		res.update({
			'custom_description': self.custom_description,
			'name': self.custom_description,
		})
		return res

	def _check_discontinued_stock(self):
		for line in self:
			product = line.product_id
			if not product:
				continue
			if product.product_tmpl_id.is_product_variant and product.product_tmpl_id.type != 'consu' and not product.is_storable:
				continue
			warehouse = line.order_id.warehouse_id or self.env['stock.warehouse'].search([('company_id','=',self.order_id.company_id.id or self.env.company.id)], limit=1)
			if warehouse:
				free_qty = product.with_context(warehouse_id=warehouse.id).free_qty
				if product.is_discontinued and free_qty <= 0:
					raise ValidationError(_(
						"The product '%s' is discontinued and has no stock in warehouse '%s'."
					) % (product.display_name, warehouse.name))

	@api.model_create_multi
	def create(self, vals_list):
		lines = super().create(vals_list)
		lines._check_discontinued_stock()
		return lines

	def write(self, vals):
		res = super().write(vals)
		self._check_discontinued_stock()
		return res