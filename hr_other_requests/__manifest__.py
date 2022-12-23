# -*- coding: utf-8 -*-
# Created By ENG-Mahmoud Ramadan
{
    'name': "HR Other Requests",

    'summary': """Module to Make Employee Request any request not found in the system""",

    'description': """
       Module to Make Employee Request any request not found in the system
    """,

    'author': "E.Mudathir",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'hr',
    'version': '1.0.8',

    # any module necessary for this one to work correctly
    'depends': ['ext_hr_employee'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/other_request_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
}
