from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date


class LibraryBook(models.Model):
    _name = 'library.book'
    _description = 'Library Book'
    _order = 'create_date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Basic Info
    name = fields.Char(string='Title', required=True, tracking=True)
    isbn = fields.Char(string='ISBN')
    author = fields.Char(string='Author', required=True, tracking=True)
    publisher = fields.Char(string='Publisher')
    publication_year = fields.Integer(string='Publication Year')
    edition = fields.Char(string='Edition')
    pages = fields.Integer(string='Number of Pages')
    borrow_price = fields.Float(string='Borrowing Price', required=True, tracking=True, help="Cost to borrow this book.")
    book_id = fields.Many2one(
    'library.book', 
    string='Book', 
    required=True, 
    tracking=True
)
    language = fields.Selection([
        ('ar', 'Arabic'),
        ('en', 'English'),
        ('fr', 'French'),
        ('es', 'Spanish'),
    ], string='Language', default='ar')

    status = fields.Selection([
        ('available', 'Available'),
        ('checked_out', 'Checked Out'),
        ('maintenance', 'Under Maintenance')
    ], string='Status', default='available', tracking=True)

    rating = fields.Selection([
        ('1' , '★☆☆☆☆'),
        ('2' , '★★☆☆☆'),
        ('3' , '★★★☆☆'),
        ('4' , '★★★★☆'),
        ('5' , '★★★★★')
    ], string='Rating')


    notes = fields.Text(string='Notes')
    added_date = fields.Date(string='Added Date', default=fields.Date.today)

    last_borrowed_date = fields.Date(string='Last Borrowed', compute='_compute_last_borrowed')

    # Relations
    current_borrowing_id = fields.Many2one(
        'library.borrowing',
        string='Current Borrowing',
        compute='_compute_current_borrowing',
        store=True
    )
    borrowing_ids = fields.One2many(
        'library.borrowing',
        'book_id',
        string='Borrowings'
    )

    # Computed Fields
    is_available = fields.Boolean(string='Is Available', compute='_compute_availability')

    total_borrowings = fields.Integer(string='Total Times Borrowed', compute='_compute_borrowing_stats')
    popularity_score = fields.Float(string='Popularity Score', compute='_compute_borrowing_stats')

    active_borrowers_count = fields.Integer(
        string='Active Borrowers',
        compute='_compute_borrowers_count'
    )
    total_borrowers_count = fields.Integer(
        string='Total Borrowers',
        compute='_compute_borrowers_count'
    )
    current_borrower_ids = fields.Many2many(
        'library.member',
        string='Current Borrowers',
        compute='_compute_current_borrowers'
    )

    @api.depends('status')
    def _compute_availability(self):
        for book in self:
            book.is_available = (book.status == 'available')

    @api.depends('borrowing_ids', 'borrowing_ids.returned')
    def _compute_current_borrowing(self):
        for book in self:
            borrowing = self.env['library.borrowing'].search([
                ('book_id', '=', book.id),
                ('returned', '=', False)
            ], limit=1)
            book.current_borrowing_id = borrowing

    @api.depends('borrowing_ids')
    def _compute_borrowing_stats(self):
        for book in self:
            book.total_borrowings = len(book.borrowing_ids)
            # Simple popularity score based on number of borrowings
            book.popularity_score = book.total_borrowings * 0.1

    @api.depends('borrowing_ids.borrow_date')
    def _compute_last_borrowed(self):
        for book in self:
            last_borrowing = self.env['library.borrowing'].search([
                ('book_id', '=', book.id)
            ], order='borrow_date desc', limit=1)
            book.last_borrowed_date = last_borrowing.borrow_date if last_borrowing else False

    @api.depends('borrowing_ids.member_id', 'borrowing_ids.returned')
    def _compute_borrowers_count(self):
        for book in self:
            # Count active borrowers (currently borrowing)
            active_borrowings = book.borrowing_ids.filtered(lambda b: not b.returned)
            book.active_borrowers_count = len(active_borrowings.mapped('member_id'))

            # Count total unique borrowers
            all_borrowers = book.borrowing_ids.mapped('member_id')
            book.total_borrowers_count = len(set(all_borrowers.ids))

    @api.depends('borrowing_ids.member_id', 'borrowing_ids.returned')
    def _compute_current_borrowers(self):
        for book in self:
            active_borrowings = book.borrowing_ids.filtered(lambda b: not b.returned)
            book.current_borrower_ids = active_borrowings.mapped('member_id')

    # SQL Constraints
    _sql_constraints = [
        ('isbn_unique', 'unique(isbn)', 'The ISBN must be unique!')
    ]

    # Date Validation
    @api.constrains('added_date')
    def _check_added_date(self):
        for record in self:
            if record.added_date and record.added_date > date.today():
                raise ValidationError(_('The added date cannot be in the future.'))

    @api.constrains('publication_year')
    def _check_publication_year(self):
        for record in self:
            if record.publication_year and record.publication_year > date.today().year:
                raise ValidationError(_('Publication year cannot be in the future.'))

    # Rating Validation (string-based check)

    @api.constrains('rating')
    def _check_rating_value(self):
        valid_values = ['1', '2', '3', '4', '5']
        for book in self:
            if book.rating and str(book.rating) not in valid_values:
                raise ValidationError(_("Invalid rating value for book '%s'.") % book.name)

    # Actions
    def action_mark_available(self):
        self.write({'status': 'available'})

    def action_mark_checked_out(self):
        self.write({'status': 'checked_out'})

    def action_mark_maintenance(self):
        self.write({'status': 'maintenance'})

    def action_quick_borrow(self):
        """Quick action to borrow this book"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Borrow %s') % self.name,
            'res_model': 'library.book.borrow.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_book_ids': [(6, 0, [self.id])],
            }
        }

    def action_view_borrowers(self):
        """Smart button action - Show borrowers in Kanban view grouped by member"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Borrowers of "%s"') % self.name,
            'res_model': 'library.borrowing',
            'view_mode': 'kanban,tree,form',
            'domain': [('book_id', '=', self.id)],
            'context': {
                'default_book_id': self.id,
                'search_default_group_by_member': 1,
                'group_by': 'member_id',
            },
            'target': 'current',
        }

    def action_view_borrowing_history(self):
        """Smart button action - Show complete borrowing history"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Borrowing History of "%s"') % self.name,
            'res_model': 'library.borrowing',
            'view_mode': 'tree,form,graph,pivot',
            'domain': [('book_id', '=', self.id)],
            'context': {
                'default_book_id': self.id,
                'search_default_filter_active': 1,
            },
        }
    # Display format for dropdowns and relations
    def name_get(self):
        result = []
        for book in self:
            display_name = "{} - {}".format(book.name, book.author)
            result.append((book.id, display_name))
        return result
