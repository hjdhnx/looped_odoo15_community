""" Initialize Custody Renewal """
from odoo import _, fields, models
from odoo.exceptions import UserError


class CustodyRenewal(models.TransientModel):
    """ Initialize Custody Renewal """
    _name = 'custody.renewal'
    _description = 'Custody Renewal'

    returned_date = fields.Date(string='Renewal Date', required=1)

    def proceed(self):
        """ Renew custody request """
        context = self.env.context
        custody_obj = self.env[context.get('active_model')]
        custody_ids = custody_obj.browse(context.get('active_ids'))
        if self.returned_date <= custody_ids.date_request:
            raise UserError(_('Please give valid renewal date'))
        custody_ids.write({'renew_return_date': True,
                           'renew_date': self.returned_date,
                           'state': 'to_approve'})
