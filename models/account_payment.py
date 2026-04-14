from odoo import _, fields, models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    cashbox_auto_transfer_session_id = fields.Many2one(
        "account.cashbox.session",
        string="Sesión de cierre (auto-transferencia)",
        readonly=True,
        copy=False,
        help="Sesión de caja que generó esta transferencia automática al cierre.",
    )

    def _create_paired_internal_transfer_payment(self):
        if self.env.context.get("auto_transfer_keep_paired_draft"):
            # Crear el paired payment pero dejarlo en borrador
            for payment in self:
                paired_payment_type = "inbound" if payment.payment_type == "outbound" else "outbound"
                paired_payment = payment.copy(
                    {
                        "journal_id": payment.destination_journal_id.id,
                        "company_id": payment.destination_journal_id.company_id.id,
                        "destination_company_id": payment.company_id.id,
                        "destination_journal_id": payment.journal_id.id,
                        "payment_type": paired_payment_type,
                        "payment_method_line_id": payment.destination_journal_id._get_available_payment_method_lines(
                            paired_payment_type
                        )[:1].id,
                        "move_id": None,
                        "memo": payment.memo,
                        "paired_internal_transfer_payment_id": payment.id,
                        "date": payment.date,
                        "cashbox_auto_transfer_session_id": payment.cashbox_auto_transfer_session_id.id,
                    }
                )
                paired_payment._compute_payment_method_line_id()
                payment.paired_internal_transfer_payment_id = paired_payment

                body = _("This payment has been created from:") + payment._get_html_link()
                paired_payment.message_post(body=body)
                body = _("A second payment has been created:") + paired_payment._get_html_link()
                payment.message_post(body=body)
            return
        return super()._create_paired_internal_transfer_payment()
