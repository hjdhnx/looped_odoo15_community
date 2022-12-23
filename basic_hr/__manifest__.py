# -*- coding: utf-8 -*-

{
    'name': "Basic for HR changes",
    'summary': """  """,
    'sequence': 0,
    'description': """  """,
    'author': "OserGroup",
    'website': "http://www.osergroup.com",
    'category': 'account',
    'version': '0.1',
    'depends': [
        'base',
        'account',
        'hr',
        'hr_contract'
    ],
    'data': [
        # 'security/security.xml',
        'security/ir.model.access.csv',
        'views/basic_hr.xml',
    ],
    'demo': [
        # 'demo.xml',
    ]
}
