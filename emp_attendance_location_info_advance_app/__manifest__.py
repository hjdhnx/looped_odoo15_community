# -*- coding: utf-8 -*-

{
    "name" : "Employee Attendance Geo Location Information",
    "author": "Edge Technologies",
    "version" : "15.0.1.0",
    "live_test_url":'https://youtu.be/kXCJMyjLOtc',
    "images":["static/description/main_screenshot.png"],
    'summary': 'Employee Attendance with Google Map Employee Attendance location Information for employee Attendance with map location for attendance sign in location of employee user location sign in location of sign in employee login location attendance geo location',
    "description": """
    
    This app helps to add the login and logout message track employee login location with co-ordinates and with the link of google map.
    
    """,
    "license" : "OPL-1",
    "depends" : ['base','hr','web','hr_attendance','emp_attendance_google_map_app'],
    "data": [
        'views/employee_map_attendance_view.xml',
    ],
    'external_dependencies' : {
        'python' : ['googlegeocoder','googlemaps' , 'geopy'],
    },

    "demo": [],

    "assets": {
        "web.assets_backend": [
            "emp_attendance_location_info_advance_app/static/src/js/my_attendances.js",
        ],

        "web.assets_qweb": [
            "emp_attendance_location_info_advance_app/static/src/xml/my_attendances_extend_template.xml",
        ],
    },

    "auto_install": False,
    "installable": True,
    "price": 45,
    "currency": 'EUR',
    "category" : "Human Resources",
    
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
