""" Initialize Custody report """
from odoo import fields, models, tools


# pylint: disable=no-self-use,sql-injection
class CustodyHistory(models.Model):
    """ Initialize Custody report """
    _name = "report.custody"
    _description = "Custody Analysis"
    _auto = False

    name = fields.Char()
    date_request = fields.Date(string='Requested Date')
    employee = fields.Many2one('hr.employee', check_company=True)
    purpose = fields.Char(string='Reason')
    custody_name = fields.Many2one('custody.property', check_company=True)
    item_id = fields.Many2one('custody.item', check_company=True)
    return_date = fields.Date()
    renew_date = fields.Date(string='Renewal Return Date')
    renew_return_date = fields.Boolean(string='Renewal Return Date')
    state = fields.Selection(
        [('draft', 'Draft'),
         ('to_approve', 'Waiting For Approval'),
         ('approved', 'Approved'),
         ('returned', 'Returned'),
         ('rejected', 'Refused')], string='Status'
    )

    _order = 'name desc'

    def _select(self):
        """ Select query """
        select_str = """
             SELECT
                    (select 1 ) AS nbr,
                    t.id as id,
                    t.name as name,
                    t.date_request as date_request,
                    t.employee as employee,
                    t.purpose as purpose,
                    t.custody_name as custody_name,
                    t.item_id as item_id,
                    t.return_date as return_date,
                    t.renew_date as renew_date,
                    t.renew_return_date as renew_return_date,
                    t.state as state
        """
        return select_str

    def _group_by(self):
        """ Group query """
        group_by_str = """
                GROUP BY
                    t.id,
                    name,
                    date_request,
                    employee,
                    purpose,
                    custody_name,
                    item_id,
                    return_date,
                    renew_date,
                    renew_return_date,
                    state
        """
        return group_by_str

    def init(self):
        """ Initialize and execute query """
        tools.sql.drop_view_if_exists(self._cr, 'report_custody')
        self._cr.execute("""
            CREATE view report_custody as %s FROM hr_custody t %s
        """ % (self._select(), self._group_by()))
