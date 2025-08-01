{
    'name': 'Custom Sale Order',
    'version': '1.0',
    'category': 'Sales',
    'summary': 'Customize Sale Order',
    
    'description': """
        This module customizes the Sale Order to remove the 'Create' option when creating customers.
    """,
    
    'depends': [ 'sale','product','purchase','product_customization'],
    
    'data': [
        'views/sale_order.xml',
        'views/report.xml',
     ],

    'assets': {
        'web.assets_backend': [
            'sale_customization/static/src/css/app.css',
        ]
           
    },
    
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3'
}