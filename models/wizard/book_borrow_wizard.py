from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
# from datetime import timedelta , date


class BookBorrowWizard(models.TransientModel):
    _name = 'library.book.borrow.wizard'
    _description = 'Book Borrowing Wizard'

    member_id = fields.Many2one('library.member', string='Member', required=True)
    book_ids = fields.Many2many('library.book', string='Books to Borrow')
    borrow_date = fields.Date(string='Borrow Date', default=fields.Date.context_today)
    due_date = fields.Date(string='Due Date', default=fields.Date.context_today)
    notes = fields.Text(string='Notes')

    # @api.model
    # def default_get(self, fields):
    #     # res = super().default_get(fields)
    #     # if 'due_date' in fields:
    #     #     res['due_date'] = fields.Date.today() + timedelta(days=14)
    #     return date.today() + timedelta(days=14)

    # @api.onchange('borrow_date')
    # def _onchange_borrow_date(self):
    #     """Update due date when borrow date changes"""
    #     if self.borrow_date:
    #         borrow_date = fields.Date.from_string(self.borrow_date)
    #         self.due_date = borrow_date + timedelta(days=14)

    def action_borrow_books(self):
        """Create borrowing records for selected books"""
        self.ensure_one()

        if not self.book_ids:
            raise ValidationError(_("Please select at least one book to borrow."))

        # Check book availability
        unavailable_books = self.book_ids.filtered(lambda b: b.status != 'available')
        if unavailable_books:
            raise ValidationError(_(
                "The following books are not available: %s") %
                                  ', '.join(unavailable_books.mapped('name'))
                                  )

        # Create borrowing records
        Borrowing = self.env['library.borrowing']
        for book in self.book_ids:
            borrowing_vals = {
                'member_id': self.member_id.id,
                'book_id': book.id,
                'borrow_date': self.borrow_date,
                'due_date': self.due_date,
                'notes': self.notes,
            }
            Borrowing.create(borrowing_vals)

        # Show success message
        book_names = ', '.join(self.book_ids.mapped('name'))
        message = _("Successfully borrowed: %s") % book_names
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': message,
                'type': 'success',
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }

    def action_open_member_form(self):
        """Open member form to create new member"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('New Member'),
            'res_model': 'library.member',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_name': 'New Member'},
        }