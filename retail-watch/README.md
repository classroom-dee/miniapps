## Usecase
**SPA**
1. User: Input search keyword + category
2. View: a list of products as search result
3. User: Select target product to observe
4. View: add it to monitoring list
5. Back: Refreshes user's product list data in the background periodically, persist in db + persist last refresh time.
6. Back: Aggregates data, persist  denormalized tables
7. BI: Per-product price line graph / all-in-one line graph

## API spec
### NS traffic
- GET /v1/search/{keyword}: search result of {keyword}
- POST /v1/monitor: add to monitoring list
### EW traffic
- GET /v1/monitor: get all the products added so far
- GET /v1/search/exact/{i}: search for the exact item with id {i}
- GET /v1/monitor/{i}: get a specific product with id {i}

## Tracing
- Decorator aggregator with context for lite telemetry
- Rate limit

# TODO
- Pagination for search result
- Use async DB
- DONT RUN THE REFRESH ROUTINE ON HTTP SERVER WITH MULTIPLE WORKERS!!!! -> Separate scheduler service
- SPA! 
- Separate project? (this is getting bigger)