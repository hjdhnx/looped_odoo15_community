from odoo import models, fields, api, _

class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    arbic_name = fields.Char('')

class posCategory(models.Model):
    _inherit = 'pos.category'

    website_image_1920 = fields.Binary()
    is_published = fields.Boolean()
    exclude_pos_ids = fields.Many2many('pos.config','pos_config_categ_rel')
    restaurant_printer_ids = fields.Many2many('restaurant.printer', 'printer_category_rel', 'category_id', 'printer_id',)
    invisible_in_ui = fields.Boolean()
    arbic_name = fields.Char('')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)  
    is_multi_company = fields.Boolean(compute='_compute_is_multi_company', store=False)
    product_ids = fields.One2many('product.template', 'pos_categ_id',)
    product_note_ids = fields.Many2many('pos.product_note',compute="_get_product_note")
    
    def _get_product_note(self):
        for rec in self:
            rec.product_note_ids = False 
            product_note_ids = rec.env['pos.product_note'].search([('pos_category_ids','in',rec.id)])
            rec.product_note_ids = product_note_ids.ids 
    def _compute_is_multi_company(self):
        multi_company = self.env['res.users'].has_group('base.group_multi_company')
        for rec in self:
            if multi_company:
                rec.is_multi_company = True
            else:
                rec.is_multi_company = False

    def action_open_product_ids(self):
        res = {
            'name': _('Products'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'product.template',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', self.product_ids.ids)],
        }
        return res            
