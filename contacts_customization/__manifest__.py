{
    'name': 'Contact customizations',
    'version': '1.0',
    'summary': 'Change Individual to CPF and Company to CNPJ',
    'author': 'Ayyan',
    'depends': ['base', 'contacts','account','base_vat','l10n_br','l10n_latam_base'],
    'data': [
        'views/views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
