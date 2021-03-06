#    Copyright (C) 2020 Compassion CH
#    @author: Quentin Gigon

from datetime import date, datetime

from babel.dates import format_timedelta

from odoo import models, api, fields


class CrowdfundingProject(models.Model):
    _name = "crowdfunding.project"
    _inherit = "website.published.mixin"
    _inherits = {'utm.campaign': 'campaign_id'}
    _description = "Crowd-funding project"

    description = fields.Text(
        "Project description",
        help="Aim of the project, why you want to create it, for which purpose and "
             "any useful information that the donors should know.",
        required=True
    )
    personal_motivation = fields.Text(
        help="Tell the others what is inspiring you, why it matters to you.",
        required=True
    )
    type = fields.Selection(
        [("individual", "Individual"), ("collective", "Collective")],
        required=True,
        default="individual",
    )
    deadline = fields.Date(
        "Deadline of project",
        help="Indicate when your project should end.",
        required=True, index=True)
    time_left = fields.Char(compute="_compute_time_left")
    cover_photo = fields.Binary(
        "Cover Photo",
        help="Upload a cover photo that represents your project. Best size: 900x400px",
        attachment=True)
    presentation_video = fields.Char(
        help="Paste any video link that showcase your project"
             " (e.g. https://vimeo.com/jlkj34ek5)"
    )
    facebook_url = fields.Char("Facebook link")
    twitter_url = fields.Char("Twitter link")
    instagram_url = fields.Char("Instagram link")
    personal_web_page_url = fields.Char("Personal web page")
    product_id = fields.Many2one(
        "product.product", "Supported fund",
        domain=[("activate_for_crowdfunding", "=", True)])
    product_number_goal = fields.Integer(compute="_compute_product_number_goal")
    product_number_reached = fields.Integer(compute="_compute_product_number_reached")
    number_sponsorships_goal = fields.Integer(
        compute="_compute_number_sponsorships_goal"
    )
    number_sponsorships_reached = fields.Integer(
        compute="_compute_number_sponsorships_reached"
    )
    sponsorship_ids = fields.Many2many(
        "recurring.contract", string="Sponsorships",
        compute="_compute_sponsorships"
    )
    invoice_line_ids = fields.One2many(
        "account.invoice.line", "crowdfunding_project_id", string="Donations"
    )
    project_owner_id = fields.Many2one("res.partner", "Project owner", required=True)
    owner_participant_id = fields.Many2one(
        "crowdfunding.participant", compute="_compute_owner_participant_id"
    )
    participant_ids = fields.One2many(
        "crowdfunding.participant", "project_id", string="Participants"
    )
    event_id = fields.Many2one("crm.event.compassion", "Event")
    campaign_id = fields.Many2one('utm.campaign', 'UTM Campaign',
                                  required=True, ondelete='cascade')
    state = fields.Selection(
        [("draft", "Draft"), ("active", "Active")],
        required=True,
        default="draft",
        readonly=True,
    )
    owner_lastname = fields.Char(string="Your lastname")
    owner_firstname = fields.Char(string="Your firstname")
    active = fields.Boolean(default=True)

    @api.model
    def create(self, vals):
        res = super().create(vals)
        event = self.env["crm.event.compassion"].create(
            {
                "name": vals.get("name"),
                "event_type_id": self.env.ref(
                    "crowdfunding_compassion.event_type_crowdfunding"
                ).id,
                "crowdfunding_project_id": res.id,
                "company_id": self.env.user.company_id.id,
                "start_date": date.today(),
                "end_date": vals.get("deadline"),
                "hold_start_date": date.today(),
                "number_allocate_children": vals.get("product_number_goal"),
                "planned_sponsorships": vals.get("number_sponsorships_goal"),
                "type": "crowdfunding",
            }
        )
        res.event_id = event

        res.add_owner2participants()

        return res

    @api.multi
    def add_owner2participants(self):
        """Add the project owner to the participant list. """
        for project in self:
            if project.project_owner_id not in project.participant_ids.mapped(
                    "partner_id"
            ):
                participant = {
                    "partner_id": project.project_owner_id.id,
                    "project_id": project.id,
                }
                project.write({"participant_ids": [(0, 0, participant)]})

    @api.multi
    def _compute_product_number_goal(self):
        for project in self:
            project.product_number_goal = sum(
                project.participant_ids.mapped('product_number_goal'))

    @api.multi
    def _compute_product_number_reached(self):
        for project in self:
            invl = project.invoice_line_ids.filtered(lambda l: l.state == "paid")
            project.product_number_reached = int(sum(invl.mapped("quantity")))

    @api.multi
    def _compute_number_sponsorships_goal(self):
        for project in self:
            project.number_sponsorships_goal = sum(
                project.participant_ids.mapped('number_sponsorships_goal'))

    @api.multi
    def _compute_sponsorships(self):
        for project in self:
            project.sponsorship_ids = self.env["recurring.contract"].search([
                ("campaign_id", "=", project.campaign_id.id),
                ("type", "like", "S"),
                ("state", "!=", "cancelled")
            ])

    @api.multi
    def _compute_number_sponsorships_reached(self):
        for project in self:
            project.number_sponsorships_reached = len(project.sponsorship_ids)

    @api.multi
    def _compute_website_url(self):
        for project in self:
            project.website_url = "/projects/create/confirm"

    @api.multi
    def _compute_time_left(self):
        for project in self:
            project.time_left = format_timedelta(
                project.deadline - date.today(), locale=self.env.lang[:2]
            )

    @api.multi
    def _compute_owner_participant_id(self):
        for project in self:
            project.owner_participant_id = project.participant_ids.filtered(
                lambda p: p.partner_id == project.project_owner_id
            ).id

    @api.multi
    def validate(self):
        self.write({"state": "active"})
        comm_obj = self.env["partner.communication.job"]
        config = self.env.ref("crowdfunding_compassion.config_project_published")
        for project in self:
            # Send email to inform project owner
            comm_obj.create(
                {
                    "config_id": config.id,
                    "partner_id": project.project_owner_id.id,
                    "object_ids": project.id,
                }
            )

    @api.model
    def get_active_projects(self, limit=None, year=None):
        if year:
            self = self.search(
                [
                    ("deadline", ">=", datetime(year, 1, 1)),
                    ("deadline", "<=", datetime(year, 12, 31)),
                ]
            )

        return self.search(
            [("state", "!=", "draft")], limit=limit, order="deadline ASC"
        )
