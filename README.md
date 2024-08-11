# Code Examples

## Asynchronous SQLite Operations
**Description:** This example demonstrates how to perform asynchronous database operations using aiosqlite in Python. It includes custom methods for interacting with a database, such as fetching, creating, and updating records.

**Key Features:**
* Asynchronous database connection and operations.
* Custom methods for CRUD operations. 
* Example code for managing users and groups.

[Code link](simple_orm.py)


## Asynchronous API Interaction with WildBerries
**Description**: This example demonstrates how to interact asynchronously with the WildBerries private API using aiohttp in Python. It includes methods for searching products, handling API errors, and processing geographic data.

**Key Features:**
* Asynchronous API requests with error handling and retries.
* Methods to search for products and handle response data. 
* Function to get geographic region IDs from coordinates. 
* Utility for generating product combinations based on price constraints.

[Code link](wildberries_private_api_wrapper.py)


## Truth Table Generator
**Description:** This example demonstrates how to create and manipulate truth tables in Python. It includes methods for generating truth tables, performing logical operations, and solving logical expressions.

**Key Features:**
* Creation and manipulation of truth tables.
* Methods for logical operations: implication, disjunction, conjunction, equation, and inversion. 
* Parsing and solving logical expressions.

[Code link](bool_math_calculator.py)


## Payment and User Management API
**Description:** This example provides various API views for handling payments and user interactions. It includes endpoints for processing payments, managing search purchases, and providing bonuses.

**Key Features:**
* PayOkPaymentAPIView: Handles PayOk payment notifications and verifies signatures.
* OxaPayPaymentAPIView: Processes OxaPay payment notifications using HMAC validation.
* BuySearchesAPIView: Allows authenticated users to purchase searches and receive payment URLs.
* BuyFullDataAPIView: Provides full data for a search if the user has made a purchase.
* GetBonusAPIView: Grants a bonus to users if they haven't used their bonus yet and validates their Telegram ID.

[Code link](django_views.py)

