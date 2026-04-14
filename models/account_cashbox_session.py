from odoo import Command, _, api, fields, models
from odoo.exceptions import UserError


class AccountCashboxSession(models.Model):
    _inherit = "account.cashbox.session"

    auto_transfer_payment_ids = fields.One2many(
        "account.payment",
        "cashbox_auto_transfer_session_id",
        string="Transferencias Automáticas",
        readonly=True,
    )

    @api.depends("cashbox_id")
    def _compute_line_ids(self):
        super()._compute_line_ids()
        for rec in self:
            auto_journal_ids = rec.cashbox_id.auto_transfer_journal_ids
            if not auto_journal_ids:
                continue
            for line in rec.line_ids:
                if line.journal_id in auto_journal_ids:
                    line.balance_start = 0.0

    def action_account_cashbox_session_close(self):
        res = super().action_account_cashbox_session_close()
        # Si super devuelve una accion (wizard de ajuste), no crear transferencias aún
        if res:
            return res
        # Si la sesión se cerró (state == closed), crear transferencias automáticas
        for session in self.filtered(lambda s: s.state == "closed"):
            session._create_auto_transfers()
        return res

    def _create_auto_transfers(self):
        self.ensure_one()
        cashbox = self.cashbox_id
        if not cashbox.auto_transfer_journal_ids or not cashbox.auto_transfer_destination_journal_id:
            return

        dest_journal = cashbox.auto_transfer_destination_journal_id
        for source_journal in cashbox.auto_transfer_journal_ids:
            # Calcular el monto de la sesión para este diario
            line = self.line_ids.filtered(lambda l: l.journal_id == source_journal)
            if not line:
                continue
            amount = line.balance_end
            if amount <= 0:
                continue

            # Crear el pago de transferencia (lado salida - se postea)
            # No asignamos cashbox_session_id para evitar la validación de sesión abierta
            # La trazabilidad se mantiene con cashbox_auto_transfer_session_id
            payment_vals = {
                "payment_type": "outbound",
                "is_internal_transfer": True,
                "journal_id": source_journal.id,
                "destination_journal_id": dest_journal.id,
                "amount": amount,
                "date": fields.Date.context_today(self),
                "memo": _("Cierre sesión %s", self.name),
                "cashbox_auto_transfer_session_id": self.id,
            }
            payment = self.env["account.payment"].sudo().create(payment_vals)
            # Postear el lado salida (esto normalmente crea y postea el paired payment)
            # Usamos contexto para que el paired se quede en draft
            payment.with_context(
                auto_transfer_keep_paired_draft=True,
            ).action_post()
