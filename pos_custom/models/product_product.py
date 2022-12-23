# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import datetime, timedelta

class Available_Apps(models.Model):
    _name = 'available.apps'

    name = fields.Char('')

class PosProductImage(models.Model):
    _name = 'pos.product.image'
    _inherit = 'product.image'
    _description = "Pos Product Image"

class UpdatePriceExtraWizard(models.TransientModel):
    _name = 'update.price.extra.wizard'

    value_id = fields.Many2one('product.template.attribute.value',string='')
    price_extra = fields.Float('Price Extra')
    arabic_name = fields.Char('')

    def action_ok(self): 
        if self.price_extra:   
            self.value_id.update({'price_extra': self.price_extra,})
        if self.arabic_name:
            self.value_id.update({'arabic_name': self.arabic_name})
            
class ProductTemplate(models.Model):
    _inherit = 'product.template.attribute.value'

    arabic_name = fields.Char('')

    def action_update_price_extra(self):
        view = self.env.ref('pos_custom.update_price_extra_wizard_form')
        ctx = {
                'default_value_id': self.id,
                'default_price_extra': self.price_extra,
                }        
        return {
            'name': _('Update Price Extra and Arabic name'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'update.price.extra.wizard',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': ctx,
        }        

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    invisible_in_ui = fields.Boolean()
    is_delivery_app = fields.Boolean()
    name_ar = fields.Char(string="Product Description", required=False)
    other_lang_name = fields.Char(string="Other Lang Name", )
    exclude_template_config_ids = fields.Many2many('pos.config', 'pos_config_template_rel', 'template_id', 'pos_config_id')
    open_price = fields.Boolean('Open Price')
    preparation_time = fields.Float('Preparation Time')
    product_template_value_ids = fields.Many2many('product.template.attribute.value', string="Product Attribute Values",compute='_compute_product_template_value_ids')
    pos_product_template_image_ids = fields.One2many('pos.product.image', 'product_tmpl_id', string="Pos Product Media", copy=True)
    is_extra = fields.Boolean(string="Is Extra")
    extra_products = fields.Many2many('product.product', string="Extra Products")
    is_discount = fields.Boolean(string="Is Discount")       
    product_type = fields.Selection([('normal', 'Normal'), ('is_extra', 'Is Extra'), ('is_discount', 'Is Discount'), ('has_addons', 'Has Addons'),], string='', default='normal')
    pricelist_item_ids = fields.One2many('product.pricelist.item', 'product_tmpl_id', string="",)
    available_apps_ids = fields.Many2many('available.apps', string="Available Apps")

    def _compute_product_template_value_ids(self):
        for rec in self:
            v_ids = []
            for l in rec.attribute_line_ids:
                v_ids += l.product_template_value_ids.ids
            rec.product_template_value_ids = v_ids

class ProductProduct(models.Model):
    _inherit = 'product.product'

    original_name = fields.Char(string="Variant name", compute='_compute_original_name')
    image_edit_date = fields.Datetime(default=lambda self:datetime.now())

    def write(self, vals):
        if 'is_extra' in vals and vals.get('is_extra'):
            vals['extra_products'] = False

        if 'image_1920' in vals:
            vals['image_edit_date'] = datetime.now() 
            

        return super(ProductProduct, self).write(vals)

    def _compute_original_name(self):
        names = dict(self.name_get())
        for product in self:
            product.original_name = names.get(product.id) or product.name
            
class ProductTemplate(models.Model):
    _inherit = 'product.template'

    image_edit_date = fields.Datetime(default=lambda self:datetime.now() )

    def write(self, vals):
        
        if 'image_1920' in vals:
            vals['image_edit_date'] = datetime.now() 
            

        return super(ProductTemplate, self).write(vals)
