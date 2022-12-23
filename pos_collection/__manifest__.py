# -*- coding: utf-8 -*-
{
    'name': "POS Collection",

    'summary': """
        POS Collection""",

    'description': """
        POS Collection
    """,

    'author': "E.Mudathir",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'POS',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['petty_cash_aggregate_report','point_of_sale'],

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/pos_config_views.xml',
        'views/templates.xml',
        'wizard/pos_collection_wizard_view.xml',
        'wizard/pos_collection_accountant_wizard_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
