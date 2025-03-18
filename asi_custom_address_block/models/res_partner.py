from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'

    ref = fields.Char()

    ADDRESS_FIELDS = ('street', 'street2', 'zip', 'city', 'state_id', 'country_id', 'ref')

class FormatAddressMixin(models.AbstractModel):
    _inherit = 'format.address.mixin'

    def _view_get_address(self, address_format):
        """ Override to include 'ref' in the formatted address """
        for partner in self:
            address_format = super(FormatAddressMixin, self)._view_get_address(partner)
            address_format += '\n' + partner.ref
        return address_format
