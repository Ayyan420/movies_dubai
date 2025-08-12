from odoo import _, models
from odoo.exceptions import ValidationError

class SaleOrderDiscount(models.TransientModel):
	_inherit = 'sale.order.discount'

	def action_apply_discount(self):
		self.ensure_one()
		self = self.with_company(self.company_id)

		max_discount = self.sale_order_id.max_discount or 0.0
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

		def get_discount_percentage_without_negative(order):
			normal_lines = order.order_line.filtered(
				lambda l: l.price_unit > 0 and not getattr(l.product_id, 'is_discount', False)
			)
			total_before = sum(l.price_unit * l.product_uom_qty for l in normal_lines)
			total_after = sum(
				l.price_unit * l.product_uom_qty * (1 - (l.discount or 0.0) / 100.0)
				for l in normal_lines
			)
			if total_before <= 0:
				return 0
			return ((total_before - total_after) / total_before) * 100

		current_pct = round(get_discount_percentage(self.sale_order_id),2)
		current_pct_without_lines_negative = round(get_discount_percentage_without_negative(self.sale_order_id),2)

		if self.discount_type == 'sol_discount':
			intended_pct = self.discount_percentage * 100
			new_total_pct = intended_pct
			discount_product = self._get_discount_product()
			self.sale_order_id.order_line.filtered(lambda l: l.product_id == discount_product).unlink()
			if not bypass_limit and new_total_pct > max_discount:
				raise ValidationError(
					_(f"Total discount {new_total_pct:.2f}% exceeds the allowed maximum of {max_discount}%.")
				)
			self.sale_order_id.order_line.write({'discount': 0})
			self.sale_order_id.order_line.write({'discount': intended_pct})
		elif self.discount_type in ('so_discount', 'amount'):
			discount_product = self._get_discount_product()
			self.sale_order_id.order_line.filtered(lambda l: l.product_id == discount_product).unlink()
			if self.discount_type == 'so_discount':
				intended_pct = self.discount_percentage*100
			else:
				order_total_before = sum(
					(l.price_unit * l.product_uom_qty) * (1 - (l.discount or 0.0) / 100.0)
					for l in self.sale_order_id.order_line
					if l.price_unit > 0 and not getattr(l.product_id, 'is_discount', False) and l.product_id != discount_product
				)
				intended_pct = (self.discount_amount / order_total_before) * 100 if order_total_before else 0
			new_total_pct = round(current_pct_without_lines_negative + intended_pct,2)
			if not bypass_limit and new_total_pct > max_discount:
				raise ValidationError(
					_(f"Total discount {new_total_pct:.2f}% exceeds the allowed maximum of {max_discount}%.")
				)
			self._create_discount_lines()
		return True