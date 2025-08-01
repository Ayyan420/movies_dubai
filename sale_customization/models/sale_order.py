from odoo import models, fields, api, _
from datetime import date, timedelta
from odoo.exceptions import ValidationError

class SaleOrder(models.Model):
	_inherit = 'sale.order'

	target_delivery_date = fields.Date(
		string="Target Delivery Date",
		default=lambda self: fields.Date.today(), tracking=True
	)

	payment_method_id = fields.Many2one(
		'account.payment.method',
		string='Payment Method', tracking=True
	)

	@api.onchange('order_line')
	def _compute_target_delivery_date(self):
		max_delay = 0
		today = fields.Date.today()

		for line in self.order_line:
			product = line.product_id
			required_qty = line.product_uom_qty
			if not product.is_storable:
				continue
			warehouse = line.order_id.warehouse_id or self.env['stock.warehouse'].search([], limit=1)
			if warehouse:
				stock_location = warehouse.lot_stock_id
				free_qty = product.with_context(location=stock_location.id).free_qty
				if required_qty > free_qty:
					if product.seller_ids:
						delays = [seller.delay for seller in product.seller_ids if seller.delay]
						if delays:
							product_max_delay = max(delays)
							if product_max_delay > max_delay:
								max_delay = product_max_delay
		self.target_delivery_date = today + timedelta(days=max_delay)


class SaleOrderLine(models.Model):
	_inherit = 'sale.order.line'

	product_id = fields.Many2one(
		'product.product',
		string='Product',
		domain=[('sale_ok', '=', True)],
		context={'simple_product_name': True},
		ondelete='restrict',
		check_company=True
	)

	product_default_code = fields.Char(
		string="Reference Code",
		related='product_id.default_code',
		store=True
	)

	custom_description = fields.Text(string='Name/Description')

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
			warehouse = line.order_id.warehouse_id or self.env['stock.warehouse'].search([], limit=1)
			if warehouse:
				stock_location = warehouse.lot_stock_id
				free_qty = product.with_context(location=stock_location.id).free_qty
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