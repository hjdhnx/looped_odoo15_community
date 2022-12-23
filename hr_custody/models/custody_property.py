""" Initialize Hr Custody Property """
from odoo import _, api, fields, models


class HrCustodyProperty(models.Model):
    """ Initialize Hr Custody Property """
    _name = 'custody.property'
    _description = 'Custody Property'
    _check_company_auto = True
    _sql_constraints = [
        ('unique_asset_id', 'UNIQUE(asset_id)',
         _('Custody property asset account must be unique')),
        ('unique_custody_property_name', 'UNIQUE(name,code)',
         _('Custody property must be unique')),
    ]
    name = fields.Char(required=True)
    code = fields.Char(readonly=True, default='New')
    image = fields.Image()

    desc = fields.Html()
    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company
    )
    property_type = fields.Selection(
        [('empty', 'No Connection'),
         ('asset', 'Assets'),
         ('product', 'Products')], default='empty'
    )
    asset_id = fields.Many2one('account.asset', copy=False)
    # currency_id = fields.Many2one(related='asset_id.currency_id', store=True)
    # original_value = fields.Monetary(
    #     related='asset_id.original_value', store=True)
    # book_value = fields.Monetary(related='asset_id.book_value', store=True)
    product_id = fields.Many2one('product.product', copy=False)
    item_id = fields.Many2one('custody.item', required=True, tracking=True)
    state = fields.Selection(
        [('available', 'Available'),
         ('booked', 'Booked'),
         ('received', 'Received')],
        string='Status', default='available', required=True, tracking=True
    )

    @api.onchange('product_id')
    def _onchange_product(self):
        """ set property name as product name """
        self.name = self.product_id.name

    def name_get(self):
        """ Override name_get to change display name """
        return [
            (rec.id, _("[%s] %s") % (rec.code, rec.name))
            for rec in self
        ]

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """ Override name_search to change search with name and code """
        args = args or []
        domain = []
        if name:
            domain = ['|', ('code', operator, name), ('name', operator, name)]
        records = self.search(domain + args, limit=limit)
        return records.name_get()

    # pylint: disable=arguments-differ
    @api.model
    def create(self, vals):
        """ Override create method to sequence name """
        if vals.get('code', 'New') == 'New':
            vals['code'] = self.env['ir.sequence'].next_by_code(
                'custody.property') or '/'
        return super(HrCustodyProperty, self).create(vals)
