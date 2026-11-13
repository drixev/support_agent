# Error reference
## ERR_INVALID_PAYLOAD
The request body failed schema validation. Check the `details` field for the offending property.
## ERR_TICKET_LOCKED
The ticket is being edited by another agent. Wait until the lock is released (max 5 minutes) and try again.
## Webhooks
If your endpoint does not answer within 10 seconds, delivery is retried up to 5 times.