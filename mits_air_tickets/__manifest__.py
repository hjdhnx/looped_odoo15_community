# -*- coding: utf-8 -*-
{
    'name': "Mits Air Tickets",

    'summary': """
        Mits Air Tickets""",

    'description': """
        Mits Air Tickets
    """,

    'author': "OserGroup",
    'website': "http://www.osergroup.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'HR',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base',
                'hr',
                'hr_holidays',
                'ext_hr_employee',
                'ext_hr_contract',
                'mits_hr_leaves',
                'hr_attendance_excuse',
                # 'hr_gosi',
                ],

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/tickets_sequence.xml',
        'views/late_request_type_view.xml',
    ],
}