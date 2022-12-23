# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Extend HR Contract',
    'version': '1.1',
    'summary': 'Adding new fields in HR contract',
    'sequence': 30,
    'author': "OserGroup",
    'website': "http://www.osergroup.com",
    'description': "",
    'category': 'Human Resources',
    'depends': ['base', 'hr', 'ext_hr_employee', 'hr_contract',
    #after select payroll module after migration uncomment
    'hr_payroll',
    'hr_payroll_account'
     ],
    'data': [
        #need migrate after select payroll
        'data/hr_payroll_data.xml',
        'views/hr_contract_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
