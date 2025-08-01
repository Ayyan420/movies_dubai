{
    'name': 'Custom Sale Order',
    'version': '1.0',
    'category': 'Sales',
    'summary': 'Customize Sale Order',
    
    'description': """
        This module customizes the Sale Order to remove the 'Create' option when creating customers.
    """,
    
    'depends': [ 'sale','product','purchase','sale_customization'],
    
    'data': [
        'views/move.xml',
        'views/report_invoice_inherit.xml',
    ],
    
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3'
}