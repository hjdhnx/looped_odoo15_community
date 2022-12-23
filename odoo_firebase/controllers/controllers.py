# -*- coding: utf-8 -*-
# from odoo import http


# class OdooFirebase(http.Controller):
#     @http.route('/odoo_firebase/odoo_firebase', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/odoo_firebase/odoo_firebase/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('odoo_firebase.listing', {
#             'root': '/odoo_firebase/odoo_firebase',
#             'objects': http.request.env['odoo_firebase.odoo_firebase'].search([]),
#         })

#     @http.route('/odoo_firebase/odoo_firebase/objects/<model("odoo_firebase.odoo_firebase"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('odoo_firebase.object', {
#             'object': obj
#         })
