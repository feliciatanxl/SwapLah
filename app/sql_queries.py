"""Bulky read-query SQL for offers, transactions, and reports.

These string constants live outside ``app/db.py`` to keep that module focused
and comfortably under its size budget. They are imported back into ``db`` and
used exactly as before.
"""

OFFERS_FOR_SELLER_SQL = (
    "SELECT offers.id,offers.listing_id,offers.buyer_id,offers.offer_type,"
    "offers.proposed_price,offers.swap_listing_id,offers.status,"
    "offers.created_at,listings.title AS listing_title,"
    "listings.category AS listing_category,listings.price AS listing_price,"
    "listings.seller_id AS seller_id,"
    "buyer.display_name AS buyer_display_name,seller.display_name AS seller_display_name,"
    "swap_listing.title AS swap_listing_title FROM offers "
    "JOIN listings ON offers.listing_id=listings.id "
    "JOIN users AS buyer ON offers.buyer_id=buyer.id "
    "JOIN users AS seller ON listings.seller_id=seller.id "
    "LEFT JOIN listings AS swap_listing ON offers.swap_listing_id=swap_listing.id "
    "WHERE listings.seller_id=? AND offers.status='Pending' ORDER BY offers.created_at DESC"
)

ALL_OFFERS_SQL = (
    "SELECT offers.id,offers.listing_id,offers.buyer_id,offers.offer_type,"
    "offers.proposed_price,offers.swap_listing_id,offers.status,"
    "offers.created_at,listings.title AS listing_title,"
    "listings.category AS listing_category,listings.price AS listing_price,"
    "listings.seller_id AS seller_id,"
    "buyer.display_name AS buyer_display_name,seller.display_name AS seller_display_name,"
    "swap_listing.title AS swap_listing_title FROM offers "
    "JOIN listings ON offers.listing_id=listings.id "
    "JOIN users AS buyer ON offers.buyer_id=buyer.id "
    "JOIN users AS seller ON listings.seller_id=seller.id "
    "LEFT JOIN listings AS swap_listing ON offers.swap_listing_id=swap_listing.id "
    "WHERE offers.status='Pending' ORDER BY offers.created_at DESC"
)

RESOLVED_OFFERS_FOR_USER_SQL = (
    "SELECT offers.id,offers.listing_id,offers.buyer_id,offers.offer_type,"
    "offers.proposed_price,offers.swap_listing_id,offers.status,"
    "offers.created_at,listings.title AS listing_title,"
    "listings.category AS listing_category,listings.price AS listing_price,"
    "buyer.display_name AS buyer_display_name,seller.display_name AS seller_display_name,"
    "swap_listing.title AS swap_listing_title FROM offers "
    "JOIN listings ON offers.listing_id=listings.id "
    "JOIN users AS buyer ON offers.buyer_id=buyer.id "
    "JOIN users AS seller ON listings.seller_id=seller.id "
    "LEFT JOIN listings AS swap_listing ON offers.swap_listing_id=swap_listing.id "
    "WHERE offers.status!='Pending' AND (offers.buyer_id=? OR listings.seller_id=?) "
    "ORDER BY offers.created_at DESC"
)

ALL_RESOLVED_OFFERS_SQL = (
    "SELECT offers.id,offers.listing_id,offers.buyer_id,offers.offer_type,"
    "offers.proposed_price,offers.swap_listing_id,offers.status,"
    "offers.created_at,listings.title AS listing_title,"
    "listings.category AS listing_category,listings.price AS listing_price,"
    "buyer.display_name AS buyer_display_name,seller.display_name AS seller_display_name,"
    "swap_listing.title AS swap_listing_title FROM offers "
    "JOIN listings ON offers.listing_id=listings.id "
    "JOIN users AS buyer ON offers.buyer_id=buyer.id "
    "JOIN users AS seller ON listings.seller_id=seller.id "
    "LEFT JOIN listings AS swap_listing ON offers.swap_listing_id=swap_listing.id "
    "WHERE offers.status!='Pending' ORDER BY offers.created_at DESC"
)

# Correlated subqueries flagging whether the current participant reviewed the
# offer; {reviewer} is either 'buyer_id' or 'seller_id'.
_REVIEWED_BY_SQL = (
    "(SELECT COUNT(*) FROM reviews WHERE reviews.offer_id=transactions.offer_id "
    "AND reviews.reviewer_id=transactions.{reviewer}) AS has_reviewed,"
    "(SELECT reviews.created_at FROM reviews WHERE reviews.offer_id=transactions.offer_id "
    "AND reviews.reviewer_id=transactions.{reviewer} ORDER BY reviews.id DESC LIMIT 1) AS reviewed_at"
)

TRANSACTIONS_FOR_BUYER_SQL = (
    "SELECT transactions.id,transactions.offer_id,transactions.transaction_type,transactions.amount,"
    "transactions.created_at,listings.title AS listing_title,"
    "listings.category AS listing_category,"
    "seller.display_name AS counterparty_display_name,"
    f"{_REVIEWED_BY_SQL.format(reviewer='buyer_id')} FROM transactions "
    "JOIN listings ON transactions.listing_id=listings.id "
    "JOIN users AS seller ON transactions.seller_id=seller.id "
    "WHERE transactions.buyer_id=? ORDER BY transactions.created_at DESC"
)

TRANSACTIONS_FOR_SELLER_SQL = (
    "SELECT transactions.id,transactions.offer_id,transactions.transaction_type,transactions.amount,"
    "transactions.created_at,listings.title AS listing_title,"
    "listings.category AS listing_category,"
    "buyer.display_name AS counterparty_display_name,"
    f"{_REVIEWED_BY_SQL.format(reviewer='seller_id')} FROM transactions "
    "JOIN listings ON transactions.listing_id=listings.id "
    "JOIN users AS buyer ON transactions.buyer_id=buyer.id "
    "WHERE transactions.seller_id=? ORDER BY transactions.created_at DESC"
)

GET_ALL_REPORTS_SQL = (
    "SELECT r.id,r.listing_id,r.reporter_id,r.reason,r.description,"
    "r.status,r.created_at,COALESCE(l.title,'Deleted Listing') as listing_title,"
    "COALESCE(l.category,'Unknown') as listing_category,"
    "COALESCE(u.display_name,'Unknown User') as reporter_display_name "
    "FROM reports r LEFT JOIN listings l ON r.listing_id=l.id "
    "LEFT JOIN users u ON r.reporter_id=u.id ORDER BY r.created_at DESC"
)
