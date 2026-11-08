# Sales data, 2025

Exported from the order system on 5 January 2026 by Hugo Lambert (Financial Controller).

## orders_2025.csv

One row per order line placed between 1 January and 31 December 2025.

| Column | Meaning |
| --- | --- |
| `order_id` | Unique order reference, `SO-25-nnnnn`. |
| `order_date` | Date the order was placed (not the delivery date). |
| `channel` | `Dealer` (sold through an authorised dealer), `Direct` (arvenne.com webshop) or `Fleet` (B2B contract). |
| `country` | Delivery country, ISO code (`UK` is used for the United Kingdom). |
| `dealer_id` | Dealer reference for `Dealer` orders, see `dealers_2025.xlsx`. Empty otherwise. |
| `customer` | Fleet customer name. Empty for other channels. |
| `model` | Model ordered. |
| `quantity` | Bikes on the line. |
| `unit_price` | List price per bike **excluding VAT**, in the order currency, on the order date. |
| `currency` | `EUR`, `CHF` (Switzerland) or `GBP` (United Kingdom). |
| `discount_pct` | Discount off the list price: the dealer's tier discount for dealer orders, the negotiated rebate for fleet orders, promotions for direct orders. |
| `status` | `Delivered`, `Cancelled` (never shipped) or `Returned` (refunded in full). |

## Definitions used in every report

- **Net revenue** of a line = `quantity × unit_price × (1 − discount_pct / 100)`, in the order currency.
- Revenue and unit figures count **Delivered** lines only. Cancelled and Returned lines count as zero.
- Amounts in CHF and GBP are converted to euros with the budget exchange rates (Finance, `budget_2025.xlsx`, sheet *Assumptions*), dividing the local amount by the rate.
- The webshop sells only to France, Germany, the Netherlands and Belgium. Switzerland, the United Kingdom and Austria are served by dealers and fleet contracts.
- Fleet contracts are managed by Ben Whitaker.
