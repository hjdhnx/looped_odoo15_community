# pylint: disable=missing-docstring,manifest-required-author
{
    'name': 'Custody Management',
    'summary': 'Custody Management',
    'author': 'Muhamed Abd El-Rhman, CORE B.P.O',
    'website': 'http://www.core-bpo.com',
    'version': '13.0.1.0.0',
    'category': 'Human Resources',
    'license': 'AGPL-3',
    'depends': [
        'ext_hr_employee',
        # account_asset
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'wizard/reject_reason.xml',
        'wizard/custody_renewal.xml',
        'views/account_account.xml',
        # 'views/account_asset.xml',
        'views/account_move.xml',
        'views/hr_custody.xml',
        'views/custody_item.xml',
        'views/custody_property.xml',
        'views/hr_employee.xml',
        'data/ir_cron.xml',
        'data/ir_sequence.xml',
        # 'data/mail_activity_type.xml',
        'data/mail_template.xml',
        'reports/custody_report.xml'
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
