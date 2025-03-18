from odoo import models, fields

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    project_responsible = fields.Many2one('res.users', string='Responsable del Proyecto')
    asi_sign = fields.Binary(string='Firma ASI')
    client_sign = fields.Binary(string='Firma del Cliente')
    customer_signer_id = fields.Many2one('res.partner', 'Firmada por', domain="[('parent_id', '=', partner_id)]", tracking=True) 
    responsible_employee = fields.Many2one('res.users', string='Firmado por:', default=lambda self: self.env.user.sale_team_id.user_id.parent_id)
