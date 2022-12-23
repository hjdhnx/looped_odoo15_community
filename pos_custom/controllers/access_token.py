import hashlib
import logging
import os
from datetime import datetime, timedelta
from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

token_expiry_date_in = "pos_custom.access_token_token_expiry_date_in"

def random_token(length=40, prefix="access_token"):
    rbytes = os.urandom(length)
    return "{}_{}".format(prefix, str(hashlib.sha1(rbytes).hexdigest()))

class APIAccessToken(models.Model):
    _name = "api.access_token"
    _description = "API Access Token"

    token = fields.Char("Access Token", required=True)
    user_id = fields.Many2one("res.users", string="User", required=True, ondelete='cascade',)
    token_expiry_date = fields.Datetime(string="Token Expiry Date", required=True)
    scope = fields.Char(string="Scope")

    def find_or_create_token(self, user_id=None, create=False):
        if not user_id:
            user_id = self.env.user.id
        access_token = self.env["api.access_token"].sudo().search([("user_id", "=", user_id)], order="id DESC", limit=1)
        if access_token:
            access_token = access_token[0]
            if access_token.has_expired():
                access_token = None
        if not access_token and create:
            token_expiry_date = datetime.now() + timedelta(days=365) + timedelta(hours=2)
            vals = {
                    "user_id": user_id,
                    "scope": "userinfo",
                    # "token_expiry_date": token_expiry_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                    "token_expiry_date": token_expiry_date,
                    "token": random_token(),
                    }
            access_token = self.env["api.access_token"].sudo().create(vals)
        if not access_token:
            return None
        return access_token

    def is_valid(self, scopes=None):
        """Checks if the access token is valid."""
        self.ensure_one()
        return not self.has_expired() and self._allow_scopes(scopes)

    def has_expired(self):
        self.ensure_one()
        return datetime.now() > fields.Datetime.from_string(self.token_expiry_date)

    def _allow_scopes(self, scopes):
        self.ensure_one()
        if not scopes:
            return True
        provided_scopes = set(self.scope.split())
        resource_scopes = set(scopes)
        return resource_scopes.issubset(provided_scopes)

class Users(models.Model):
    _inherit = "res.users"

    token_ids = fields.One2many("api.access_token", "user_id", string="Access Tokens")
    is_portal = fields.Boolean('')

    @api.constrains('groups_id')
    def _check_one_user_type(self):
        """We check that no users are both portal and users (same with public).
           This could typically happen because of implied groups.
        """
        user_types_category = self.env.ref('base.module_category_user_type', raise_if_not_found=False)
        user_types_groups = self.env['res.groups'].search(
            [('category_id', '=', user_types_category.id)]) if user_types_category else False
        if user_types_groups:  # needed at install
            pass
            # if self._has_multiple_groups(user_types_groups.ids):
            #     raise ValidationError(_('The user cannot have more than one user types.'))

    def del_groups_internal(self):
        return
        if self.is_portal:
            group_portal = self.env['res.groups'].search([('name', '=', 'Portal')], limit=1)
            self._cr.execute('DELETE FROM res_groups_users_rel WHERE uid = %(user_id)s and gid != %(group_id)s ;' 
                , {'user_id': self.id, 'group_id': group_portal.id})
  
