# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, fields, tools, _

testing = tools.config.get('test_enable')


if not testing:
    # prevent these forms to be registered when running tests

    class EventRegistrationForm(models.AbstractModel):
        _name = 'cms.form.event.registration'
        _inherit = 'cms.form.match.partner'

        _form_model = 'event.registration'
        _form_model_fields = [
            'name', 'phone', 'email', 'event_id',
        ]
        _form_required_fields = ['partner_lastname', 'partner_firstname',
                                 'partner_email']

        form_buttons_template = 'cms_form_compassion.modal_form_buttons'
        form_id = 'modal_compassion_event_registration'
        event_id = fields.Many2one('event.event')

        @property
        def form_msg_success_created(self):
            # No success message as we have a confirmation page
            return False

        @property
        def _form_fieldsets(self):
            return [
                {
                    'id': 'coordinates',
                    'fields': [
                        'partner_lastname', 'partner_firstname',
                        'partner_email', 'partner_phone',
                        'partner_zip', 'partner_city', 'partner_country_id'
                    ]
                }
            ]

        @property
        def form_title(self):
            return _("Registration for ") + self.event_id.name

        @property
        def submit_text(self):
            return _("Register now")

        def form_init(self, request, main_object=None, **kw):
            form = super(EventRegistrationForm, self).form_init(
                request, main_object, **kw)
            # Set default values
            form.event_id = kw.get('event').odoo_event_id
            return form

        def form_before_create_or_update(self, values, extra_values):
            super(EventRegistrationForm, self).form_before_create_or_update(
                values, extra_values
            )
            name = extra_values.get('partner_lastname', '') + ' ' + \
                extra_values.get('partner_firstname', '')
            values.update({
                'name': name,
                'phone': extra_values.get('partner_phone'),
                'email': extra_values.get('partner_email'),
                'event_id': self.event_id.id,
                'event_ticket_id': self.event_id.valid_ticket_ids[:1].id,
                'user_id': self.event_id.user_id.id,
            })

        def _form_create(self, values):
            """Just create the main object (as superuser)."""
            # pass a copy to avoid pollution of initial values by odoo
            self.main_object = self.form_model.sudo().create(values.copy())

        def form_next_url(self, main_object=None):
            return '/event/{}/registration/{}/success'.format(
                self.main_object.event_id.id, self.main_object.id)