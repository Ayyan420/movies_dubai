{
    'name': 'Sale Order Customizations',
    'version': '1.0',
    'category': 'Sales',
    'depends': [
        'sale',
        'product',
        'account',
        'mail',
        'base',
        'accounting_customization',
        'delivery'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/own_delivery_days.xml',
        'views/report.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3'
}
