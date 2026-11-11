class DomainError(Exception):
    """Base de Errores de dominio"""
    
class TicketNotFoundError(DomainError):
    def __init__(self, ticket_id:str) -> None:
        super().__init__(f"Ticket {ticket_id} not found")
        self.ticket_id = ticket_id
