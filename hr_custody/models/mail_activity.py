""" init object mail.activity """

from odoo import _, models
from odoo.exceptions import UserError


class MailActivity(models.Model):
    """ init object mail.activity """

    _inherit = 'mail.activity'

    # pylint: disable=no-member
    def action_feedback(self, feedback=False, attachment_ids=None):
        """
        Override Action Feedback.
        :param feedback:<string>
        :param attachment_ids:<attachment>
        :return:
        """
        ctx = self.env.context
        receipt_type_id = self.env.ref('hr_custody.'
                                       'activity_type_custody_receipt')
        return_type_id = self.env.ref('hr_custody.'
                                      'activity_type_custody_return')
        custody_type_list = receipt_type_id + return_type_id
        if not receipt_type_id or not return_type_id:
            raise UserError(_('Activity Type Custody Receipt Or '
                              'Return Not Found.'))
        for activity in self:
            if self.env.user != activity.user_id and \
                    activity.res_model in ['hr.custody'] and \
                    activity.activity_type_id in custody_type_list:
                raise UserError(_('Only Assigned User Can '
                                  'Mark Activity Related to Custody As done.'))
            if activity.res_id and self.env.user == activity.user_id and \
                    activity.res_model in ['hr.custody'] and \
                    activity.activity_type_id == receipt_type_id:
                custody = self.env['hr.custody'].browse(activity.res_id)
                if custody.custody_name.state == 'booked':
                    custody.custody_name.update({'state': 'received'})
            if activity.res_id and self.env.user == activity.user_id and \
                    activity.res_model in ['hr.custody'] and \
                    activity.activity_type_id == return_type_id \
                    and not ctx.get('manual_return'):
                custody = self.env['hr.custody'].browse(activity.res_id)
                if custody.custody_name.state == 'received':
                    custody.with_context(
                        {'activity_action': True}).action_return()
        return super(MailActivity, self).action_feedback(
            feedback, attachment_ids
        )
