# -*- coding: utf-8 -*-
{
    'name': "Installment Menu",

    'summary': """
        Add Loans Installement Menu""",

    'description': """
        Add Loans Installement Menu
    """,

    'author': "Saad El Waradany",
    'website': "saad.wardany@gmail.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Loans',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr', 'hr_loans'],

    # always loaded
    'data': [
        'views/views.xml',
    ],
}