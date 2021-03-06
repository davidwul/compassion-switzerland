#    Copyright (C) 2020 Compassion CH
#    @author: Quentin Gigon

from odoo import models, fields


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    crowdfunding_participant_id = fields.Many2one(
        "crowdfunding.participant", "Crowdfunding participant"
    )
    crowdfunding_project_id = fields.Many2one(
        "crowdfunding.project", "Crowdfunding project"
    )
    is_anonymous = fields.Boolean(default=False)
