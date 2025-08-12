from odoo import models, fields, api
from odoo.osv import expression

class ProductTEMP(models.Model):
	_inherit = 'product.template'
	
	@api.model
	def name_search(self, name='', args=None, operator='ilike', limit=100):
		args = args or []
		domain = []
		if name:
			domain = [('name', operator, name)]
			variants = self.env['product.product'].search([
				'|', '|',
				('default_code', operator, name),
				('barcode', operator, name),
				('name', operator, name)
			])
			if variants:
				variant_template_ids = variants.mapped('product_tmpl_id').ids
				domain = expression.OR([domain, [('id', 'in', variant_template_ids)]])
			vendor_partners = self.env['res.partner'].search(
				[('name', operator, name)], limit=None
			)
			if vendor_partners:
				supplierinfos = self.env['product.supplierinfo'].search([
					('partner_id', 'in', vendor_partners.ids)
				])
				product_templates_by_vendor = supplierinfos.mapped('product_tmpl_id')
				domain = expression.OR([domain, [('id', 'in', product_templates_by_vendor.ids)]])
		final_domain = expression.AND([domain, args])
		records = self.search(final_domain, limit=limit)
		return [(r.id, r.display_name) for r in records]


class ProductProduct(models.Model):
	_inherit = 'product.product'

	is_discontinued = fields.Boolean(string='Discontinued Variant', default=False, tracking=True)

	@api.model
	def name_search(self, name='', args=None, operator='ilike', limit=100):
		args = args or []
		domain = []
		if name:
			domain = [
				'|', '|', '|',
				('name', operator, name),
				('default_code', operator, name),
				('barcode', operator, name),
				('product_tmpl_id.name', operator, name),
			]
			vendor_partners = self.env['res.partner'].search(
				[('name', operator, name)], limit=None
			)
			if vendor_partners:
				supplierinfos = self.env['product.supplierinfo'].search([
					('partner_id', 'in', vendor_partners.ids)
				])
				product_templates = supplierinfos.mapped('product_tmpl_id')
				domain = expression.OR([
					domain,
					[('product_tmpl_id', 'in', product_templates.ids)]
				])
		final_domain = expression.AND([domain, args])
		records = self.search(final_domain, limit=limit)
		return [(record.id, record.display_name) for record in records]