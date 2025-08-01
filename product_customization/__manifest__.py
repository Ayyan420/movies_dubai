{
    'name': 'Discontinued Product Variant Control',
    'version': '1.0.0',
    'summary': 'Hide discontinued product variants from sale once stock is zero',
    'description': """
        This module adds a checkbox to product variants to mark them as discontinued.
        If the stock is 0 and variant is marked as discontinued, it will not appear in sales.
    """,
    'category': 'Sales',
    'author': 'Your Name',
    'website': 'https://yourcompany.com',
    'depends': ['product', 'sale', 'stock','sale_management'],
    'data': [
        'views/product_product_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3'
}
