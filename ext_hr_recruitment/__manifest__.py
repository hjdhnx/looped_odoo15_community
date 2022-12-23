# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Extend HR Recruitment',
    'version': '1.1',
    'summary': 'Adding new fields in Applications',
    'sequence': 30,
    'description': "",
    'category': 'Human Resources',
    'author': "OserGroup",
    'website': "http://www.osergroup.com",
    'depends': ['hr', 'hr_recruitment'],
    'data': [
        'views/ext_hr_recruitment_view.xml',
        # 'views/report_view.xml',
        'views/sequence.xml',
        # 'reports/report_job_offer.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}