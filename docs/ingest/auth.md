# Authentication
## API keys
All requests must include the header `X-API-Key`. Keys are created in the dashboard under Settings > Developers. Keys never expire but can be revoked at any time.
## OAuth tokens
For user-scoped access use OAuth 2.0 with the authorization code flow. Access tokens expire after 60 minutes; use the refresh token to obtain a new one.