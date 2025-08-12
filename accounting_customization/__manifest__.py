{
    'name': 'Accounting Cutomizations',
    'version': '1.0',
    'category': 'Sales',
    'author': 'Ayyan',
    'depends': ['sale', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'views/payment_methods.xml',
        'views/views.xml',
        'views/report.xml',
        'views/account_payment.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3'
}