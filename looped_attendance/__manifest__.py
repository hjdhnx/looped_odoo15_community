# -*- coding: utf-8 -*-
{
    'name': "Looped Attendance",

    'summary': """
        This Addons to receiving requests from ZK Devices and store in System""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Looped Team",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Attendances',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['hr_attendance','looped_menus'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/attendance_log.xml',
        'views/attendance_device.xml',
    ],

}
