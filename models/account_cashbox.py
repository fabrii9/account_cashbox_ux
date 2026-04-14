from odoo import fields, models


class AccountCashbox(models.Model):
    _inherit = "account.cashbox"

    auto_transfer_journal_ids = fields.Many2many(
        "account.journal",
        relation="cashbox_auto_transfer_journal_rel",
        column1="cashbox_id",
        column2="journal_id",
        string="Diarios Origen",
        domain="[('id', 'in', journal_ids)]",
        help="Diarios de efectivo desde los cuales se creará una transferencia automática al cerrar la sesión.",
    )
    auto_transfer_destination_journal_id = fields.Many2one(
        "account.journal",
        string="Diario Destino",
        domain="[('type', 'in', ['bank', 'cash']), ('id', 'not in', journal_ids)]",
        check_company=True,
        help="Diario al que se transferirá automáticamente el dinero recaudado al cerrar la sesión.",
    )
