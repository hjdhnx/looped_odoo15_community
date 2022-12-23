""" Initialize Hr Custody Item as property category """
from odoo import _, fields, models


class HrCustodyItem(models.Model):
    """ Initialize Hr Custody Item as property category """
    _name = 'custody.item'
    _description = 'Custody Item'
    _inherit = ['mail.thread']
    _check_company_auto = True
    _sql_constraints = [
        ('unique_custody_item_name', 'UNIQUE(name)',
         _('Custody item must be unique')),
    ]

    name = fields.Char(required=True, tracking=True)
    property_ids = fields.One2many(
        'custody.property', 'item_id', string='Properties', tracking=True
    )
    image = fields.Binary(attachment=True, tracking=True)
    description = fields.Html(tracking=True)
    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company, tracking=True
    )
