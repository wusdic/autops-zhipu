"""Ticket domain repository."""
from app.common.repository import BaseRepository
from app.domains.ticket.models import Ticket, TicketComment


class TicketRepo(BaseRepository):
    def __init__(self, session): super().__init__(session, Ticket)

class TicketCommentRepo(BaseRepository):
    def __init__(self, session): super().__init__(session, TicketComment)
