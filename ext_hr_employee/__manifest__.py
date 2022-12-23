# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Extend HR',
    'version': '1.1',
    'summary': 'Adding new fields in HR',
    'sequence': 30,
    'description': "",
    'category': 'Human Resources',
    'author': "OserGroup",
    'website': "http://www.osergroup.com",
    'depends': ['base',
                'hr',
                'hr_contract',
                ],
    'data': [
        'security/ir.model.access.csv',
        'data/hr_seq.xml',
        'views/hr_view.xml',
        'views/departments.xml',
        'views/res_config_settings_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
