# Rate limits
## Default quotas
The free plan allows 100 requests per minute per API key. The pro plan allows 1000 requests per minute.
## Handling throttling
When you exceed the quota the API returns HTTP 429 with error code ERR_QUOTA_EXCEEDED and a Retry-After header. Clients should wait and retry with exponential backoff.