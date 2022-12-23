# -*- coding: utf-8 -*-
# Created By ENG-Mahmoud Ramadan
{
    'name': "HR Attendance Excuse",

    'summary': """Hr attendance Excuse""",

    'description': """
        Hr attendance Excuse
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'hr',
    'version': '1.0.8',

    # any module necessary for this one to work correctly
    'depends': ['surgi_attendance_sheet'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/late_request.xml',
        'views/late_request_type.xml',
        'views/hr_employee_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
}
