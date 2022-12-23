# -*- coding: utf-8 -*-
{
    'name': "Dashboard Ninja Advance",

    'summary': """
    This app allow you to present your complex data in form of Charts or list view on Dashboards with awesome
                        query feature of Dashboard Ninja.
    """,

    'description': """
        Best Odoo Dashboard Apps
        Slider Dashboard Apps
        Odoo Query Dashboard Apps
        Display Dashboard Apps
        All in One Dashboard
        TV Dashboard Apps
        List View Layout
        Dashboards item Slider
        Full Screen Dashboard Item
        TV View Dashboard
        Custom Database View
        Complex Data Dashboard
        Different Models Dashboard
        Multi Models Data
        Custom Report Dashboard
        Multi Report Dashboard
        Complex Data Item
        Slider Report
        Multiple Table in Single Dashboard
        Bulk Data in Single Dashboard
        Graph View Dashboard Apps
        Pie Chart Dashboard Apps
        Widget View Dashboard
        Best Odoo Apps
        Dashboard For Websites
        Odoo Dashboard apps
        Dashboard apps
        Dashboards for Websites
        HR Dashboard Apps
        Sales Dashboard Apps
        inventory Dashboard Apps
        Lead Dashboards
        Opportunity Dashboards
        CRM Dashboards
        Best POS Apps
        POS Dashboards
        Web Dynamic Apps,
        Report Import/Export,
        Date Filter Apps
        Tile Dashboard Apps
        Dashboard Widgets,
        Dashboard Manager Apps,
        Debranding Apps
        Customize Dashboard Apps
        Charts Dashboard Apps
        Invoice Dashboard Apps
        Project management Apps
        Visualization charts
        Finance Dashboard
        Accounting Report
        Accounting Valuation
        Accounting Quantities
        Dashboard for Odoo
        Accounting Metrics
        Expense Dashboard Apps
        Invoicing Dashboard
        Vendor Payable Report
        Stock management System
        Purchase Order Dashboards
        Sales Order Dashboards
        Stock Alert Apps
        Inventory Alert Apps
        Product Dashboard
        Sales Dashboard
        Best Dashboard Apps
        Inventory Report
        Inventory Valuation
        Inventory Quantities
        V15 Dashboard
        Dashboard v15.0,
        Odoo Dashboard v15.0
        New Odoo Dashboard Apps
        Dashboard Ninja Advance

    """,

    'author': "Ksolves India Ltd.",
    'license': 'OPL-1',
    'currency': 'EUR',
    'price': 149,
    'website': "https://www.ksolves.com",
    'maintainer': 'Ksolves India Limited',
    'live_test_url': 'https://dashboardninja14.kappso.com/web/demo_login',
    'category': 'Tools',
    'version': '15.0.1.0.1',
    'support': 'sales@ksolves.com',
    'images': ['static/description/banner.gif'],

    'depends': ['ks_dashboard_ninja'],
    'assets': {


        'web.assets_backend': [
            '/ks_dn_advance/static/src/css/ks_tv_dashboard.css',
            '/ks_dn_advance/static/lib/css/owl.carousel.min.css',
            '/ks_dn_advance/static/src/js/ks_labels.js',
            '/ks_dn_advance/static/src/js/ks_ylabels.js',
            '/ks_dn_advance/static/src/js/ks_dashboard_ninja_tv_graph_preview.js',
            '/ks_dn_advance/static/src/js/ks_dashboard_ninja_tv_list_preview.js',
            '/ks_dn_advance/static/src/js/ks_tv_dashboard.js',
            '/ks_dn_advance/static/lib/js/owl.carousel.min.js',

        ],
        'web.assets_frontend': [
            '/ks_dn_advance/static/src/js/ks_website_dashboard.js',

        ],
        'web.assets_qweb': [
            '/ks_dn_advance/static/src/xml/ks_dashboard_tv_ninja.xml',
            '/ks_dn_advance/static/src/xml/ks_query_templates.xml',
        ],
    },

    'data': [
        # 'views/ks_dashboard_tv_assets.xml',
        'views/ks_dashboard_ninja_item_view_inherit.xml',
    ],

    # 'qweb': [
    #     'static/src/xml/ks_dashboard_tv_ninja.xml',
    #     'static/src/xml/ks_query_templates.xml',
    # ],


}
