# -*- coding: utf-8 -*-
{
    'name': "employee_payroll_report",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "LOOPED",
    'website': "https://loopedsol.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr_attendance'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'wizard/employee_payroll_wizard.xml',
        'views/report_confg.xml',
        'views/report_template.xml',
        'report/payslip_report_config.xml',
        'report/payslip_report_template.xml',

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
