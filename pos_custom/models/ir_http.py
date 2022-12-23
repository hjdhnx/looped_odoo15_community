# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import hashlib
import json

import odoo
from odoo import api, http, models
from odoo.http import request
from odoo.tools import file_open, image_process, ustr

from odoo.addons.web.controllers.main import HomeStaticTemplateHelpers

from odoo.addons.web.controllers.main import Binary
class Http(models.AbstractModel):
    _inherit = 'ir.http'
    
    @api.model
    def _content_image(self, xmlid=None, model='ir.attachment', res_id=None, field='datas',
            filename_field='name', unique=None, filename=None, mimetype=None, download=None,
            width=0, height=0, crop=False, quality=0, access_token=None, **kwargs):
        """
        override with sudo
        """
        status, headers, image_base64 = self.sudo().binary_content(
            xmlid=xmlid, model=model, id=res_id, field=field, unique=unique, filename=filename,
            filename_field=filename_field, download=download, mimetype=mimetype,
            default_mimetype='image/png', access_token=access_token
        )
        return self.sudo()._content_image_get_response(
            status, headers, image_base64, model=model, field=field, download=download,
            width=width, height=height, crop=crop, quality=quality)
            
            
            
            

class Binary(odoo.addons.web.controllers.main.Binary):

    @http.route(['/web/image',
        '/web/image/<string:xmlid>',
        '/web/image/<string:xmlid>/<string:filename>',
        '/web/image/<string:xmlid>/<int:width>x<int:height>',
        '/web/image/<string:xmlid>/<int:width>x<int:height>/<string:filename>',
        '/web/image/<string:model>/<int:id>/<string:field>',
        '/web/image/<string:model>/<int:id>/<string:field>/<string:filename>',
        '/web/image/<string:model>/<int:id>/<string:field>/<int:width>x<int:height>',
        '/web/image/<string:model>/<int:id>/<string:field>/<int:width>x<int:height>/<string:filename>',
        '/web/image/<int:id>',
        '/web/image/<int:id>/<string:filename>',
        '/web/image/<int:id>/<int:width>x<int:height>',
        '/web/image/<int:id>/<int:width>x<int:height>/<string:filename>',
        '/web/image/<int:id>-<string:unique>',
        '/web/image/<int:id>-<string:unique>/<string:filename>',
        '/web/image/<int:id>-<string:unique>/<int:width>x<int:height>',
        '/web/image/<int:id>-<string:unique>/<int:width>x<int:height>/<string:filename>'], type='http', auth="none")
    def content_image(self, xmlid=None, model='ir.attachment', id=None, field='datas',
                      filename_field='name', unique=None, filename=None, mimetype=None,
                      download=None, width=0, height=0, crop=False, access_token=None,
                      **kwargs):
        # 1/0
        # other kwargs are ignored on purpose
        return request.env['ir.http'].sudo()._content_image(xmlid=xmlid, model=model, res_id=id, field=field,
            filename_field=filename_field, unique=unique, filename=filename, mimetype=mimetype,
            download=download, width=width, height=height, crop=crop,
            quality=int(kwargs.get('quality', 0)), access_token=access_token)

