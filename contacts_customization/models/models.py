from odoo import models, fields, api

class ResPartner(models.Model):
	_inherit = 'res.partner'

	company_type = fields.Selection(
		selection=[
			('person', 'CPF'),
			('company', 'CNPJ'),
		],
		string='Type of Person',
		default='person',
		required=True,
		tracking=True
	)

	cpf = fields.Char(string="CPF Number", size=14,tracking=True)
	type = fields.Selection(default="contact",tracking=True)
	building_number = fields.Char(string='Building Number',tracking=True)
	apartment_number = fields.Char(string='Apartment/House Number',tracking=True)
	company_parent_id = fields.Many2one('res.partner',string='CNPJ Company Name',tracking=True)

	_sql_constraints = [
		('cpf_uniq', 'unique (cpf)', "CPF/CNPJ already exists!"),
	]

	def fields_get(self, allfields=None, attributes=None):
		res = super().fields_get(allfields, attributes)
		if 'type' in res:
			res['type']['selection'] = [
				('contact', 'Client Address'),
				('delivery', 'Delivery Address'),
			]
		return res

	@api.model
	def default_get(self, fields):
		res = super().default_get(fields)
		if 'type' in fields:
			res['type'] = 'contact'
		if 'country_id' in fields:
			res['country_id'] = self.env['res.country'].sudo().search([('code','=','BR')],limit=1).id
		if 'name' in fields and self.env.context.get('default_parent_id'):
			parent = self.env['res.partner'].browse(self.env.context.get('default_parent_id'))
			res['name'] = parent.name
		return res

	@api.model
	def name_search(self, name='', args=None, operator='ilike', limit=100):
		args = args or []
		if name and name.isdigit():
			domain = [('cpf', operator, name)] + args
			partners = self.search(domain, limit=limit)
			return partners.name_get()
		return super(ResPartner, self).name_search(name, args, operator, limit)


	def name_get(self):
		result = []
		for partner in self:
			name = partner.name or ''
			result.append((partner.id, name))
		return result