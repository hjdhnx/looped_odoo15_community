# -*- coding: utf-8 -*-
{
    'name': "MITS Document Management",

    'summary': """
        MITS Document Management""",

    'description': """
        MITS Document Management
    """,

    'author': "OserGroup",
    'website': "http://www.osergroup.com",
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'HR',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','hr'],

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/holder_sequence.xml',
        'views/headers/deliver_receive_doc_header.xml',
        'reports/deliver_receive_doc.xml',
    ],
}