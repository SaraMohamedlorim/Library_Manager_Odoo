from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class BookReturnWizard(models.TransientModel):
    _name = 'library.book.return.wizard'
    _description = 'Book Return Wizard'

    member_id = fields.Many2one('library.member', string='Member')
    borrowing_ids = fields.Many2many(
        'library.borrowing',
        string='Books to Return',
        domain="[('member_id', '=', member_id), ('returned', '=', False)]"
    )
    return_date = fields.Date(string='Return Date', default=fields.Date.today)
    apply_fine = fields.Boolean(string='Apply Fine for Overdue')
    fine_amount = fields.Float(string='Fine Amount', compute='_compute_fine_amount')
    notes = fields.Text(string='Return Notes')

    @api.depends('borrowing_ids', 'return_date')
    def _compute_fine_amount(self):
        for wizard in self:
            total_fine = 0
            for borrowing in wizard.borrowing_ids:
                if borrowing.due_date and wizard.return_date:
                    if wizard.return_date > borrowing.due_date:
                        days_overdue = (wizard.return_date - borrowing.due_date).days
                        # Fine calculation: 5 currency units per day
                        total_fine += days_overdue * 5
            wizard.fine_amount = total_fine

    @api.onchange('member_id')
    def _onchange_member_id(self):
        if self.member_id:
            active_borrowings = self.env['library.borrowing'].search([
                ('member_id', '=', self.member_id.id),
                ('returned', '=', False)
            ])
            self.borrowing_ids = active_borrowings

    def action_return_books(self):
        """Return selected books"""
        self.ensure_one()

        if not self.borrowing_ids:
            raise ValidationError(_("Please select at least one book to return."))

        returned_books = []
        for borrowing in self.borrowing_ids:
            borrowing.write({
                'returned': True,
                'return_date': self.return_date,
            })
            returned_books.append(borrowing.book_id.name)

        # Show success message
        book_names = ', '.join(returned_books)
        message = _("Successfully returned: %s") % book_names

        if self.fine_amount > 0 and self.apply_fine:
            message += _("\nTotal fine applied: %s") % self.fine_amount

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': message,
                'type': 'success',
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }