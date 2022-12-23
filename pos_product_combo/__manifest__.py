{
    'name': 'POS Product Combo',
    'summary': 'POS Product Combo',
    'author': 'IT-ARM',
    "website": "http://dgtera.com",
    'version': '15.0.0.1.0',
    'category': 'Point of Sale',
    'license': 'AGPL-3',
        'depends': ['pos_restaurant', 'sale', 'pos_custom','pos_product_calories'],

    'data': [
        'security/ir.model.access.csv',
        'views/product_template.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
