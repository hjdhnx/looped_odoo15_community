# pylint: disable=missing-docstring, manifest-required-author
{
    'name': 'Heights Custom Report',
    'summary': 'Heights Project Updates',
    'author': "Samah Kandil,HIGHTS",
    'website': "http://www.core-bpo.com",
    'category': 'tool',
    'version': '13.0.1.0.1',
    'license': 'AGPL-3',
    'depends': [
        'project',
        'project_status',
        'project_task_default_stage',
        'crm',
        'project_template',
        'bi_odoo_project_phases',
        'sale',
        'mrp',
        'stock',
    ],
    'data': [
        # 'security/ir.model.access.csv',
        'report/custom_footer.xml',
        'report/custom_header.xml',
        'report/custom_layout.xml',
        'views/res_company_views.xml',
    ],
    'demo': [

    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
