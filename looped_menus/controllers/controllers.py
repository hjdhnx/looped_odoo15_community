# -*- coding: utf-8 -*-
# from odoo import http


# class LoopedMenus(http.Controller):
#     @http.route('/looped_menus/looped_menus', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/looped_menus/looped_menus/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('looped_menus.listing', {
#             'root': '/looped_menus/looped_menus',
#             'objects': http.request.env['looped_menus.looped_menus'].search([]),
#         })

#     @http.route('/looped_menus/looped_menus/objects/<model("looped_menus.looped_menus"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('looped_menus.object', {
#             'object': obj
#         })
