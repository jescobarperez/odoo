from odoo import models, fields, api
from odoo.exceptions import ValidationError

class AccountMove(models.Model):
    _inherit = 'account.move'

    # Campos personalizados
    reviewed = fields.Boolean(string="Revisada", default=False, readonly=True)
    review_date = fields.Date(string="Fecha de Revisión", readonly=True)
    customer_signer_id = fields.Many2one(
        'res.partner',
        string="Firmante del Cliente",
        domain="[('can_sign_invoices', '=', True)]",
        help="Persona autorizada para firmar facturas por parte del cliente."
    )
    amount_in_words = fields.Char(string='Importe en Letras', compute='_compute_amount_in_words', store=True )               

    # Método para marcar la factura como revisada
                 
    def mark_as_reviewed(self):
        self.write({
            'reviewed': True,
            'review_date': fields.Datetime.now(),
        })

    # Restricción para evitar que se marque como revisada una factura no publicada
    @api.constrains('reviewed')
    def _check_reviewed_state(self):
        for move in self:
            if move.reviewed and move.state != 'posted':
                raise ValidationError("Solo se pueden revisar facturas en estado 'Publicado'.")        

      
    @api.depends('amount_total')
    def _compute_amount_in_words(self):
        for move in self:
            amount = abs(move.amount_total)
            currency = move.currency_id
            amount_in_words = currency.amount_to_text(amount) 
            move.amount_in_words = amount_in_words.capitalize()

        
    def action_post(self):
        for invoice in self:
            last_invoice = self.search([('state', '=', 'posted'), ('move_type', '=', 'out_invoice')], order='invoice_date desc', limit=1)
            if last_invoice and invoice.invoice_date < last_invoice.invoice_date:
                raise ValidationError("La fecha de la factura debe ser mayor o igual que la fecha de la ultima factura confirmada.")
        return super(AccountInvoice, self).action_post()
