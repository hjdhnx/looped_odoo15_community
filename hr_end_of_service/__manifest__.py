# -*- coding: utf-8 -*-
{
    'name': "HR End Of Service",

    'summary': """
       End of Service For Employee
       """,

    'description': """
          End of Service For Employee
    """,

    'author': "E.Mudathir",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'HR',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['mits_hr_leaves','hr_loans','hr_gratuity_settlement',
    'petty_cash_management','hr_custody',
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'data/sequence.xml',
        'views/views.xml',
        'views/hr_contract_view.xml',
        'views/templates.xml',
        'views/configuration.xml',
    ],
    
    
}
