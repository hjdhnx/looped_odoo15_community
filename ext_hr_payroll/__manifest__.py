# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Extend HR Payroll',
    'version': '1.1',
    'summary': 'Adding new fields in HR payroll',
    'sequence': 30,
    'description': "",
    'category': 'Human Resources',
    'author': "OserGroup",
    'website': "http://www.osergroup.com",
    'depends': ['hr_holidays', 'basic_hr', 'ext_hr_contract', ],
    # hr_payroll_account
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/hr_payroll_view.xml',
        'views/salary_structure_data.xml',
        'views/res_config_settings_views.xml',
        'wizard/payroll_wizard.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
