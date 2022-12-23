# -*- coding: utf-8 -*-
from openerp import http

# class FileSave(http.Controller):
#     @http.route('/file_save/file_save/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/file_save/file_save/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('file_save.listing', {
#             'root': '/file_save/file_save',
#             'objects': http.request.env['file_save.file_save'].search([]),
#         })

#     @http.route('/file_save/file_save/objects/<model("file_save.file_save"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('file_save.object', {
#             'object': obj
#         })