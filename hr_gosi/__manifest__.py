# -*- coding: utf-8 -*-

{
    'name': "HR GOSI",
    'summary': """ Gosi """,
    'sequence': 0,
    'description': """ Gosi """,
    'author': "OserGroup",
    'website': "http://www.osergroup.com",
    'category': 'hr',
    'version': '0.1',
    'depends': [
        'base',
        'hr',
        'ext_hr_contract',
        'ext_hr_employee',
        'ext_hr_payroll',
    ],
    'data': [
        # 'security/security.xml',
        'security/ir.model.access.csv',
        'views/hr_gosi.xml',
        'views/salary_structure_data.xml',
    ],
    'demo': [
        # 'demo.xml',
    ]
}
