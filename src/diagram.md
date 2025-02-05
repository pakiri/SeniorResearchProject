::: mermaid 
erDiagram
STORES  ||--o{ PRICING_INFO : sells 
STORES {
    number storeId
    string storeName
}
PRODUCTS ||--o{ PRICING_INFO : is
PRODUCTS {
    number productId
    string productName    
}
PRICING_INFO {
    number id
    number productId
    number storeId
    number zipcode
    string itemName
    string itemPrice
    string itemUnit
    date validUntil
}
:::