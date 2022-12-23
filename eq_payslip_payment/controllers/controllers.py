# -*- coding: utf-8 -*-
# from odoo import http


# class EqPayslipPayment(http.Controller):
#     @http.route('/eq_payslip_payment/eq_payslip_payment/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/eq_payslip_payment/eq_payslip_payment/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('eq_payslip_payment.listing', {
#             'root': '/eq_payslip_payment/eq_payslip_payment',
#             'objects': http.request.env['eq_payslip_payment.eq_payslip_payment'].search([]),
#         })

#     @http.route('/eq_payslip_payment/eq_payslip_payment/objects/<model("eq_payslip_payment.eq_payslip_payment"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('eq_payslip_payment.object', {
#             'object': obj
#         })
