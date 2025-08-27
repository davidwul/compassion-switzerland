##############################################################################
#
#    Copyright (C) 2014-2025 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: David Wulliamoz
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import fields, models
from odoo.tools.misc import mod10r


class ContractGroup(models.Model):
    _inherit = "recurring.contract.group"


    def _build_invoice_gen_data(
        self, invoicing_date, invoicer, gift_wizard=False
    ):
        inv_data = super()._build_invoice_gen_data(invoicing_date, invoicer,gift_wizard)
        if self.payment_mode_id.bank_account_link=="fixed":
            if self.ref[-1:]==mod10r(self.ref[:-1]):
                bank_id=self.payment_mode_id.fixed_journal_id.bank_account_id
            else:
                bank_id = self.payment_mode_id.fixed_journal_id.bank_account_id
            inv_data.update(
                {
                    "partner_bank_id": bank_id,
                }
            )
        return inv_data
