"""Integrated Tests for object hr.custody"""

from dateutil.relativedelta import relativedelta

from odoo import _, fields
from odoo.exceptions import UserError
from odoo.tests import Form, common


# pylint: disable=protected-access,too-many-locals,too-many-statements
class TestHrCustody(common.TransactionCase):
    """ Integration test for hr_custody """

    def setUp(self):
        """ Setup testing environment """
        super(TestHrCustody, self).setUp()
        self.custody_item = self.env['custody.item'].create({
            'name': 'Item'
        })
        self.fixed_asset_account = self.env['account.account'].create({
            'name': 'Item Asset',
            'code': '151010',
            'user_type_id': self.env.ref(
                'account.data_account_type_fixed_assets').id,
            'create_asset': 'draft',
            'custody_item_ids': [(4, self.custody_item.id)]
        })
        self.user = self.env.ref('base.user_admin')
        self.user_root = self.env.ref('base.user_root')
        self.partner = self.env.ref('base.res_partner_12')
        self.product = self.env.ref('product.product_product_4d')
        custody_seq = self.env.ref('hr_custody.seq_hr_custody_seq')
        property_seq = self.env.ref('hr_custody.seq_custody_property_seq')
        custody_seq.number_next_actual = 1
        property_seq.number_next_actual = 1

    def test_hr_custody(self):
        """ Test Scenario: test hr_custody """
        today = fields.Date.today()
        move_form = Form(self.env['account.move'].with_context(
            **{'default_type': 'in_invoice'}))
        move_form.partner_id = self.partner

        # Create new vendor bill with the product
        with move_form.line_ids.new() as line:
            line.product_id = self.product
            line.account_id = self.fixed_asset_account
            line.custody_item_id = self.custody_item
            line.price_unit = 500
            line.quantity = 10
        bill = move_form.save()

        # Choose fixed asset account
        bill.invoice_line_ids.write({'account_id': self.fixed_asset_account.id})

        # Post the bill to create new asset
        bill.action_post()
        assets = bill.asset_ids
        assets.account_depreciation_id = self.fixed_asset_account.id
        assets.account_depreciation_expense_id = self.fixed_asset_account.id
        self.assertTrue(assets)

        # Check that asset created with custody item
        self.assertEqual(assets.custody_item_id, self.custody_item)
        self.assertEqual(assets.custody_item_ids,
                         assets.account_asset_id.custody_item_ids)

        # Validate bill to check if property is created or not
        assets.validate()
        properties = assets.custody_property_id
        self.assertTrue(properties)
        self.assertEqual(properties.name, assets.name)
        self.assertEqual(properties.code, 'CUSPRO/000001')
        res = properties.name_search('01')
        self.assertEqual(res, [(properties.id, _("[%s] %s") %
                                (properties.code, properties.name))])

        # Create new custody
        custody = self.env['hr.custody'].with_user(self.user).create({
            'item_id': self.custody_item.id,
            'purpose': 'Just for test',
            'date_request': today + relativedelta(months=-2),
            'return_date': today + relativedelta(months=1),
        })

        # Check that custody name is in sequence
        self.assertEqual(custody.name, 'CUS/0001')

        # Check default employee
        self.assertEqual(custody.employee, self.user.employee_id)

        # Submit custody request
        custody.action_submit()
        self.assertEqual(custody.state, 'to_approve')

        # Reject custody request
        reject_reason = self.env['reject.reason'].with_context(**{
            'active_model': 'hr.custody',
            'active_ids': [custody.id]
        })
        with Form(reject_reason) as reject:
            reject.reason = 'Reject'
            reject_reason += reject.save()
        reject_reason.send_reason()
        self.assertEqual(custody.state, 'rejected')
        self.assertEqual(custody.rejected_reason, reject_reason.reason)

        # Draft custody request
        custody.action_draft()
        self.assertEqual(custody.state, 'draft')

        # Submit custody request again
        custody.action_submit()

        # Approve custody with no property
        message = _('Missing Custody Property.')
        with self.assertRaisesRegex(UserError, message):
            custody.action_approve()
        custody.custody_name = properties.id

        # Approve custody
        custody.action_approve()
        self.assertEqual(custody.state, 'approved')
        self.assertEqual(custody.custody_name.state, 'booked')
        receipt_activity = custody.activity_ids
        self.assertTrue(receipt_activity)
        message = _('Only Assigned User Can Mark '
                    'Activity Related to Custody As done.')
        with self.assertRaisesRegex(UserError, message):
            receipt_activity.with_user(self.user_root).action_feedback()
        receipt_activity.with_user(self.user).action_feedback()
        self.assertEqual(custody.custody_name.state, 'received')

        # Check employee smart buttons
        self.assertEqual(custody.employee.custody_count, 1)
        self.assertEqual(custody.employee.property_count, 1)
        action_custody = custody.employee.action_view_custody()
        action_property = custody.employee.action_view_custody_property()
        self.assertEqual(action_custody['domain'], [('id', 'in', custody.ids)])
        self.assertEqual(action_property['domain'],
                         [('id', 'in', custody.custody_name.ids)])

        # Send email
        custody.send_mail()
        self.assertTrue(custody.mail_send)

        # mail_reminder
        custody.return_date = today + relativedelta(months=-1)
        self.assertEqual(custody.mail_reminder(), custody)

        # Renew custody request
        custody_renewal = self.env['custody.renewal'].with_context(**{
            'active_model': 'hr.custody',
            'active_ids': [custody.id]
        })
        with Form(custody_renewal) as renewal:
            renewal.returned_date = today + relativedelta(months=-3)
            custody_renewal += renewal.save()
        message = _('Please give valid renewal date')
        with self.assertRaisesRegex(UserError, message):
            custody_renewal.proceed()
        custody_renewal.returned_date = \
            today + relativedelta(months=2)
        custody_renewal.proceed()
        self.assertEqual(custody.renew_return_date, True)
        self.assertEqual(custody.renew_date, custody_renewal.returned_date)
        self.assertEqual(custody.state, 'to_approve')

        # Approve renewal request
        custody.action_renew_approve()
        self.assertEqual(custody.return_date, custody_renewal.returned_date)
        self.assertEqual(custody.renew_date, False)
        self.assertEqual(custody.state, 'approved')

        # Return custody property
        return_activity = custody.activity_schedule(
            act_type_xmlid='hr_custody.activity_type_custody_return',
            date_deadline=None,
            **{'user_id': custody.employee.user_id.id}
        )
        return_activity.with_user(self.user).action_feedback()
        self.assertEqual(custody.custody_name.state, 'available')
        self.assertEqual(custody.employee.custody_count, 1)
        self.assertEqual(custody.employee.property_count, 0)
