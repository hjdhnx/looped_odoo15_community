# -*- coding: utf-8 -*-
# from odoo import http


# class HrEndOfService(http.Controller):
#     @http.route('/hr_end_of_service/hr_end_of_service/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hr_end_of_service/hr_end_of_service/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('hr_end_of_service.listing', {
#             'root': '/hr_end_of_service/hr_end_of_service',
#             'objects': http.request.env['hr_end_of_service.hr_end_of_service'].search([]),
#         })

#     @http.route('/hr_end_of_service/hr_end_of_service/objects/<model("hr_end_of_service.hr_end_of_service"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hr_end_of_service.object', {
#             'object': obj
#         })
