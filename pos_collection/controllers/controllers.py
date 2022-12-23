# -*- coding: utf-8 -*-
# from odoo import http


# class PosCollection(http.Controller):
#     @http.route('/pos_collection/pos_collection/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/pos_collection/pos_collection/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('pos_collection.listing', {
#             'root': '/pos_collection/pos_collection',
#             'objects': http.request.env['pos_collection.pos_collection'].search([]),
#         })

#     @http.route('/pos_collection/pos_collection/objects/<model("pos_collection.pos_collection"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('pos_collection.object', {
#             'object': obj
#         })
