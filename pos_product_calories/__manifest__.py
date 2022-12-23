# -*- coding: utf-8 -*-
##############################################################################
{
    'name': 'POS Calories',
    'summary': """POS Calories""",
    'version': '15.0.0.1.0',
    'description': """POS Calories""",
    'author': 'IT-ARM',
    'category': 'Point Of Sale',
    'license': 'AGPL-3',
    'depends': ['point_of_sale'],
    'data': [
        'views/pos_config_view.xml',
        'views/product.xml',
        'views/pos_order_view.xml',
        'views/product_attribute_view.xml',
    ],
    'installable': True,
    'auto_install': True,

}
