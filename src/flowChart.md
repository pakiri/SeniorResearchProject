:::mermaid
sequenceDiagram
    User->>Browser: Refresh a Store List
    Browser->>+Server: Invoke Store Scraper
    Server->>+Database: Delete all the current records
    Server->>+Server: Extract all the store information
    Server->>+Database: Load and save the pricing information
    Database->>-Server: Pricing info saved
    Server->>-Browser: Pricing info loaded
    Browser->>User: Store refreshed
:::