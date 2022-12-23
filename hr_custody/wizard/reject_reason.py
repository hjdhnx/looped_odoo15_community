""" Initialize Reject Reason """
from odoo import fields, models


class RejectReason(models.TransientModel):
    """ Initialize Reject Reason """
    _name = 'reject.reason'
    _description = 'Reject Reason'

    reason = fields.Text()

    def send_reason(self):
        """ reject reason """
        context = self.env.context
        custody_obj = self.env[context.get('active_model')]
        custody_ids = custody_obj.browse(context.get('active_ids'))
        if context.get('renew'):
            custody_ids.write({'state': 'approved',
                               'renew_reject': True,
                               'renew_rejected_reason': self.reason})
        else:
            custody_ids.write({'state': 'rejected',
                               'rejected_reason': self.reason})
