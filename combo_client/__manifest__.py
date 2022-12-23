# -*- coding: utf-8 -*-
{
    'name': "combo client",

    'summary': """ """,

    'description': """ """,

    'website': "",

    'category': 'Uncategorized',
    'version': '0.1',

    'depends': ['base','point_of_sale'],

    'data': [
        # 'security/ir.model.access.csv',
        'data/config_parameter.xml',
        'views/pos_config.xml',
    ],

    "pre_init_hook": "pre_init_check",

}
