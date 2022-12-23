""" Inherit Hr Employee to integrate custody """
from odoo import api, fields, models


class HrCustody(models.Model):
    """
        Inherit Hr Employee:
         - integrate custody.
    """
    _inherit = 'hr.employee'

    hr_custody_ids = fields.One2many(
        'hr.custody', 'employee', groups='hr.group_hr_user'
    )
    custody_count = fields.Integer(
        compute='_compute_custody', groups='hr.group_hr_user'
    )
    property_count = fields.Integer(
        compute='_compute_custody', groups='hr.group_hr_user'
    )

    @api.depends('hr_custody_ids')
    def _compute_custody(self):
        """ Compute custody value """
        for employee in self:
            employee.custody_count = len(employee.hr_custody_ids)
            approved_custody = employee.hr_custody_ids.filtered(
                lambda r: r.state == 'approved')
            employee.property_count = len(approved_custody)

    def action_view_custody(self):
        """ :return action to view custody """
        self.ensure_one()
        recs = self.mapped('hr_custody_ids')
        action = self.env.ref('hr_custody.hr_custody_action').read()[0]
        action['domain'] = [('id', 'in', recs.ids)]
        if len(recs) == 1:
            action['views'] = [(self.env.ref(
                'hr_custody.hr_custody_form').id, 'form')]
            action['res_id'] = recs.ids[0]
        return action

    def action_view_custody_property(self):
        """ :return action to view property """
        self.ensure_one()
        recs = self.hr_custody_ids.filtered(
            lambda r: r.state == 'approved').mapped('custody_name')
        action = self.env.ref('hr_custody.custody_property_action').read()[0]
        action['domain'] = [('id', 'in', recs.ids)]
        if len(recs) == 1:
            action['views'] = [(self.env.ref(
                'hr_custody.custody_property_form').id, 'form')]
            action['res_id'] = recs.ids[0]
        return action
