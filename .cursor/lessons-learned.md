*This lessons-learned file serves as a critical knowledge base for capturing and preventing mistakes. During development, document any reusable solutions, bug fixes, or important patterns using the format: [Timestamp] Category: Issue → Solution → Impact. Entries must be categorized by priority (Critical/Important/Enhancement) and include clear problem statements, solutions, prevention steps, and code examples. Only update upon user request with "lesson" trigger word. Focus on high-impact, reusable lessons that improve code quality, prevent common errors, and establish best practices. Cross-reference with @memories.md for context.*

# Lessons Learned

*Note: This file is updated only upon user request and focuses on capturing important, reusable lessons learned during development. Each entry includes a timestamp, category, and comprehensive explanation to prevent similar issues in the future.*

[2025-04-01 02:18] Infra/Debugging: Issue: Persistent systemd service startup failures (status=1/FAILURE) for FastAPI app, presenting various errors (ModuleNotFoundError, ImportError, FastAPIError, TypeError) despite multiple fixes (WorkingDirectory, PYTHONPATH, __init__.py, circular imports) → Solution: Root cause eventually identified as complex interaction between Pydantic model validation (esp. with ORM mode/from_attributes=True), SQLAlchemy relationships (esp. recursive ones), and FastAPI's dependency injection/request-response cycle during app loading. Initial assumption about `response_model` being the sole cause of `FastAPIError: Invalid args for response field` was misleading. Debugging required isolating endpoints, checking import chains, verifying schema/model correspondence, and ultimately simplifying/commenting out problematic relationships (e.g., recursive 'referrals') as a temporary workaround. → Impact: Critical for understanding that FastAPI startup errors can be misleading and stem from deep within model/schema definitions or ORM interactions, not just endpoint definitions. Emphasizes need for careful modeling of relationships in both SQLAlchemy and Pydantic, testing model validation/ORM mode compatibility early, and using iterative debugging (like commenting out code sections) to isolate complex startup issues. Recommends adding specific tests for Pydantic model loading from ORM objects. Priority: Critical.

[2025-04-01 05:03] API/Architecture: Issue: Fatal circular imports in FastAPI application, particularly between schema modules (schemas/role.py and schemas/permission.py mutually importing each other), preventing API service from starting → Solution: Implemented temporary mock API endpoints directly in main.py to bypass router-based architecture and complex schema relationships. This allowed the API service to become functional while providing time to properly refactor the schema relationships. Long-term solution requires restructuring schemas to avoid circular dependencies through: 1) Using string references for forward declarations of types, 2) Moving shared types to a common module, 3) Using Pydantic's postponed annotations, or 4) Implementing lazy imports with Type[...] annotations. → Impact: Critical for understanding how to diagnose and resolve circular imports in Python applications, especially in complex FastAPI applications with interdependent schemas. Emphasizes the need for careful design of data models to avoid circular references from the beginning, but also demonstrates the value of implementing temporary simplified solutions to keep services running while working on proper architectural fixes. Recommends schema relationship mapping early in the development process with clear dependency graphs. Priority: Critical.

[2023-11-05 10:30] Multi-Service Integration: Issue: When implementing a feature that spans multiple services (subscription system and VPN panel), keeping state consistent across services becomes challenging → Solution: Created a subscription freeze mechanism that automatically disables VPN access through PanelService integration using a proper service architecture with clearly defined responsibilities. The SubscriptionService handles business logic while delegating technical operations to PanelService through well-defined interfaces. We implemented sync_with_panel flags for operations allowing selective synchronization and proper error handling that logs but doesn't propagate panel errors to prevent cascading failures → Impact: In complex systems with multiple services, maintaining state consistency is critical. When a user freezes their subscription, their VPN access should be automatically disabled, and when they unfreeze it, access should be restored without manual intervention. This pattern of service-to-service integration with clearly defined boundaries, optional synchronization, and robust error handling prevents inconsistencies while maintaining separation of concerns. Recommends implementing comprehensive logging, transaction management, and retry mechanisms for fully reliable cross-service operations. Priority: Important.

[2023-06-21 15:42] API Design: Issue: Lack of proper rollback mechanism for multi-step operations that interact with external services → Fix: Implemented transaction-like behavior with explicit error handling and rollback steps for protocol/location change functionality → Why: Critical for maintaining data consistency between the database and external panel systems when complex operations fail midway through execution. The pattern of storing original state, tracking changes, and implementing explicit rollback logic provides a robust solution for operations that span multiple systems without ACID transaction support.

[2023-05-15 18:30] Bot Development: Issue: Managing complex multi-step user flows in Telegram bots is challenging with independent handlers → Solution: Used ConversationHandler pattern with clearly defined states (SELECTING_PAYMENT_METHOD, WAITING_FOR_PAYMENT_PROOF, etc.), persistent context storage for user data, and explicit fallback handlers for cancellation → Impact: The ConversationHandler pattern significantly improves code organization for complex flows by enforcing state transitions, preventing handler collisions, and maintaining clear user context. For Telegram bots with multi-step processes (like our purchase flow), this pattern prevents users from getting stuck in broken states, allows for precise error handling at each step, and maintains clean separation between different conversation stages. Storing user data in context.user_data during the conversation ensures continuity across states without database overhead. This approach should be used for any multi-step user interaction that requires maintaining state.

## Bot Development: My Accounts Section (August 2023)

### Lessons Learned:
1. **Conversation Structure**: Using nested ConversationHandler states is effective for complex menu systems with multiple interaction paths. The My Accounts section demonstrates how to organize navigation between list views, detail views, and action screens.

2. **Context Data Management**: Storing subscription data in `context.user_data` provides a clean way to persist information across conversation states without needing database queries for each interaction.

3. **Progress Visualization**: Using Unicode block characters to create a text-based progress bar provides a visual representation of usage statistics that works well in Telegram's text interface.

4. **Error Handling in Conversations**: Implementing consistent error handling with fallback to previous states ensures users don't get stuck in broken conversation flows when API errors occur.

5. **Callback Data Patterns**: Using prefix-based callback data patterns (like `SUBSCRIPTION_PREFIX`) makes it easier to extract IDs and route callbacks to appropriate handlers.

6. **Form Input Validation**: For text inputs (like notes or freeze reasons), providing clear instructions and cancel options gives users better control over their interactions.

7. **Async API Integration**: Using async client methods with proper error handling ensures the bot remains responsive even when backend services are slow or unavailable.

8. **Conditional UI Elements**: Dynamically adjusting UI elements based on subscription state (like showing different buttons for active vs. frozen subscriptions) improves user experience.

9. **Documentation Best Practices**: Adding comprehensive docstrings for all handler functions makes the codebase more maintainable and helps other developers understand the conversation flow.

10. **Resource Cleanup**: Explicitly clearing user data when conversations end prevents memory leaks and data inconsistencies in long-running bot instances.

## Bot Development: Payment Confirmation and Automatic Account Creation (August 2023)

### Lessons Learned:
1. **Error Resilience in Critical Flows**: When implementing payment processing and account creation, it's crucial to implement multiple layers of error handling. The payment confirmation process now includes both API-level error handling and user-facing fallback mechanisms, ensuring that even if automatic processing fails, orders can still be manually processed without data loss.

2. **Memory Management in Stateful Bots**: Using in-memory storage (like the `active_orders` dictionary) for order tracking requires careful cleanup to prevent memory leaks. We've implemented explicit cleanup after successful order processing and retain data only when manual intervention might be needed.

3. **Informative User Feedback**: For critical operations like payment processing, providing detailed feedback to both users and administrators improves the overall user experience. The implementation now shows progress updates, success confirmations with subscription details, and specific error messages when issues occur.

4. **API Function Design Patterns**: Separating API functions by domain (e.g., order-related, subscription-related) and following consistent parameter and return type patterns makes the codebase more maintainable. The new payment confirmation functions follow the established pattern of accepting IDs and returning updated objects.

5. **Stateful Processing Security**: When handling financial transactions, ensuring that orders cannot be processed multiple times is critical. The implementation now checks if orders are still active before processing and updates the UI to show who processed each payment.

6. **Fallback Mechanisms**: Adding appropriate fallback paths for when automated processes fail ensures the system remains robust. The payment confirmation now includes a fallback notification for users when automatic account creation fails, alerting them that their payment is still being processed manually.

7. **Progressive Enhancement**: When account creation succeeds, providing users with immediate details about their subscription (protocol, location, expiry date) enhances the user experience. This progressive enhancement approach gives users more information as it becomes available.

8. **Cross-Service Communication**: Implementing communication between the Telegram bot and the core API required careful handling of data transformation and error conditions. Using clear error messages and logging at each step helps with debugging cross-service issues.

[2023-08-12 12:45] Bank Card Management: Issue: Needed to implement secure bank card management with validation, ownership tracking, and priority handling → Solution: Created comprehensive bank card model with strong validation rules, appropriate indexing strategies, granular permission controls, and a priority-based display system → Why: Financial information requires robust validation and security measures; using a priority system ensures the most important cards are displayed first to users during payment processing, improving conversion rates. Implementing multiple validation layers (API, schema, database) provides defense in depth against both errors and malicious inputs. The solution also demonstrates effective use of the repository pattern with specialized CRUD operations to encapsulate database interactions.

## Bank Card Management Implementation (August 2023)

### Lessons Learned:
1. **Multi-Level Validation for Financial Data**: Implemented validation at three distinct levels (API, schema, database) to ensure complete integrity of financial data. For bank cards, this included format validation for card numbers (16 digits with proper spacing), SHEBA numbers (IR + 24 digits), and proper owner information. This multi-layered approach prevented both accidental errors and potential security issues.

2. **Priority System for Resource Rotation**: Created a priority-based display system allowing administrators to control which bank cards are shown first to users. This prevents overuse of any single card and allows for controlled rotation of payment destinations, improving payment distribution and reducing fraud risk.

3. **Specialized Status Management**: Implemented a dedicated toggle-status endpoint rather than general updates for enabling/disabling cards. This pattern provides clear audit trails of status changes and prevents accidental modification of critical status fields during general updates.

4. **Repository Pattern Benefits**: Using the repository pattern for database access provided clear separation between database operations and business logic. This made unit testing easier and will simplify future changes to the data access layer without affecting service implementations.

5. **Permission Granularity for Financial Operations**: Created fine-grained permissions specifically for financial operations rather than using general CRUD permissions. This allowed for precise control over who can view, add, modify, or delete financial instruments, enhancing security.

6. **Secure Handling of Sensitive Data**: Implemented proper masking of sensitive card information in logs and API responses, showing only partial numbers when necessary. This prevents accidental exposure of financial data while still providing enough information for identification.

7. **User Interface Considerations**: In the Telegram bot implementation, special attention was given to displaying financial information clearly with proper Persian formatting, status indicators, and confirmation steps for destructive operations like deletion.

8. **Indexing Strategy**: Created appropriate database indexes on frequently queried fields (like is_active and priority) to optimize the performance of card selection queries, especially important as the number of cards grows.

9. **Audit Trail Implementation**: Added created_at, updated_at, and last_used_at timestamps to track the lifecycle of each card, providing valuable data for both security monitoring and business intelligence.

10. **Data Transfer Object Pattern**: Used specific DTOs for different operations rather than reusing the same schema, allowing for precise control over what fields can be modified in each operation type.

These lessons demonstrate how financial feature implementation requires special consideration for security, validation, performance, and user experience beyond standard CRUD operations.

## Project Structure Consistency (April 2024)

### Lessons Learned:
1. **Consistent Directory Structure Importance**: Maintaining a consistent project structure across a mono-repo with multiple services prevents confusion and duplication. The MoonVPN project demonstrates this well with clear separation between core_api, telegram_bot, and scripts directories, each with predictable internal organization (app/models, app/services, app/api, etc.) that makes navigation intuitive.

2. **Service Layer Abstraction**: Using dedicated service classes for business logic provides a clean separation from controllers/handlers and data access. Each service (BankCardService, SubscriptionService, etc.) encapsulates related operations and handles cross-cutting concerns like validation, error handling, and transaction management, making the codebase easier to maintain.

3. **API Client Centralization**: Centralizing API calls in a single client module (api_client.py) with well-defined async functions for each endpoint creates a clean interface between services. This pattern makes it easy to update API integration points, add error handling consistently, and maintain a clear contract between frontend and backend.

4. **Conversation Flow Pattern**: Using the ConversationHandler pattern in Telegram bot handlers provides a structured approach to multi-step user interactions. Defining clear states, transitions, and data storage in context.user_data makes complex flows like card management and payment processing more maintainable and less error-prone.

5. **Consistent Error Handling**: Implementing consistent error handling patterns across the project (try/except blocks with proper logging, appropriate status code responses, user-friendly error messages) ensures that issues can be diagnosed and resolved efficiently.

6. **Progressive Enhancement Strategy**: Building the system in well-defined phases with clear task boundaries allows for progressive enhancement without rework. Each phase builds upon the previous one, with new features extending existing infrastructure rather than replacing it.

7. **Model Relationships Design**: Carefully designing model relationships (User-Role, Order-Subscription, etc.) with proper foreign keys and cascade behaviors prevents data integrity issues. The project demonstrates good practices in defining these relationships with clear intention in SQLAlchemy models.

8. **Validation at Multiple Levels**: Implementing validation at multiple levels (model constraints, service validation logic, API schema validation) provides defense in depth against invalid data while keeping each layer focused on its primary responsibility.

These lessons highlight the importance of thoughtful architecture and consistent patterns in building complex systems with multiple collaborators, including AI assistants working on different parts of the codebase.

## Payment Admin Management Implementation (April 2024)

### Lessons Learned:
1. **Load Balancing for Admin Assignment**: Implementing an intelligent load balancing system for payment verification admins required careful consideration of multiple factors. The solution uses a weighted algorithm considering card assignment, current workload, response time, and last assignment date to distribute tasks evenly. This approach prevents admin overload while ensuring timely verification of payments.

2. **Metric Tracking with Weighted Averages**: For accurate performance metrics, implementing weighted averages for response times (where newer values have proportional impact based on total processed payments) provides more accurate performance insights than simple averages. This approach allows for better tracking of admin performance improvements or degradations over time.

3. **Relationship Modeling Considerations**: The relationship between users, admins, bank cards, and groups required careful design to allow flexible assignment while maintaining data integrity. Using nullable foreign keys with appropriate cascade behaviors (CASCADE for users, SET NULL for cards) ensures system stability even when referenced entities are deleted.

4. **API Structure for Admin Operations**: Creating specialized endpoints for specific operations (like recording processed payments and selecting admins) rather than relying only on generic CRUD operations made the API more intuitive and allowed for better documentation of expected behavior. This pattern is particularly valuable for domain-specific operations that involve complex business logic.

5. **Query Optimization for Selection Logic**: The admin selection query required careful optimization with proper join conditions and ordering to ensure efficient database usage. Using SQLAlchemy's outerjoin, filter, and order_by capabilities with nulls_first/nulls_last directives allows for sophisticated selection logic with good performance characteristics even as the dataset grows.

6. **Validation at Multiple Levels**: Implementing validation at both the schema level (using Pydantic validators) and the service level provides defense in depth against invalid data. For example, the Telegram group ID validation ensures that group IDs always follow the expected format (-100...) before they reach the database.

7. **Metrics Creation Strategy**: Automatically creating metrics records when admins are first assigned (through the _ensure_metrics_exist method) prevents null reference issues in reporting and simplifies the API by eliminating the need for separate metrics creation endpoints. This pattern of "ensuring" dependent resources exist is valuable in many service implementations.

8. **Permission Granularity**: Restricting payment admin management to superusers only, rather than using more granular permissions, simplified the initial implementation while maintaining security. As the system evolves, more granular permission systems could be implemented if different admin roles need different levels of access to payment management functionality.

These lessons demonstrate how implementing domain-specific business logic requires careful consideration of data relationships, performance implications, and user experience beyond basic CRUD operations.

## Payment Proof Submission System Implementation (April 2024)

### Lessons Learned:
1. **File Storage Abstraction Layer**: Creating a dedicated FileStorageService with clear abstraction between storage logic and business logic makes the system more maintainable and adaptable. This approach separates concerns, allowing for future changes to storage backends (local filesystem, S3, etc.) without modifying the core application logic.

2. **Multi-Stage Order Status Flow**: Implementing a dedicated VERIFICATION_PENDING status in the order workflow creates a clear separation between initial submission and verification, enabling better tracking and reporting. This explicit state management prevents orders from "disappearing" in the system during the verification process and provides clear user feedback.

3. **Image Validation Security**: Implementing comprehensive image validation (file size, format, extension) at the service layer prior to storage is critical for preventing security vulnerabilities. The implementation validates both MIME type and file extension with a strict allowlist approach rather than a blocklist, which is more secure against bypass attempts.

4. **Idempotent API Design**: Designing the payment proof submission API to be idempotent allows users to safely retry operations without creating duplicate submissions. By checking the current order status before processing and allowing resubmission only in specific states (PENDING or REJECTED), the system maintains data integrity even during connection issues.

5. **Metrics Integration**: Integrating payment verification directly with admin metrics collection provides valuable insights without requiring separate tracking mechanisms. The automatic recording of verification time and approval/rejection decisions creates a complete audit trail that can be used for performance evaluation and process improvement.

6. **Error Propagation Strategy**: Using a balanced approach to error handling where critical errors are propagated while non-critical errors (like metrics recording failures) are logged but don't interrupt the primary workflow improves system reliability. This ensures that core operations succeed even if secondary features encounter issues.

7. **Field Naming Convention**: Using a consistent naming convention for related fields (e.g., payment_proof_img_url, payment_proof_submitted_at, etc.) makes the API more intuitive and simplifies query construction. This naming consistency extends to both database schema and API responses, creating a more unified developer experience.

8. **Static File Configuration**: Implementing a flexible static file mounting system that checks for directory existence and creates necessary subdirectories during startup prevents runtime errors when handling file uploads. This robust initialization process, combined with explicit error handling during file operations, ensures the system can recover from unexpected states.

These lessons underscore the importance of thoughtful system design when implementing file handling and verification workflows, particularly for financial operations where security, reliability, and auditability are paramount concerns.

## Telegram Bot Card-to-Card Payment Flow Implementation (April 2024)

### Lessons Learned:
1. **Transaction Timer Management**: Implementing a payment timeout system with automatic cleanup is essential for financial transactions. Using asyncio tasks with carefully managed lifecycle ensures that expired payment sessions are properly terminated and users are notified, preventing "ghost" transactions and improving security.

2. **Stateful Conversation Management**: Financial workflows benefit greatly from the ConversationHandler pattern with clearly defined states (SELECTING_BANK_CARD, WAITING_FOR_PAYMENT_PROOF, etc.). This creates a structured flow where each step has appropriate validation, and users cannot skip critical steps like reference number submission or skip validation.

3. **File Transfer Security**: When handling sensitive financial documents like payment receipts, implementing a secure file transfer pipeline is crucial. Downloading files as bytearrays and transmitting them directly to the API rather than storing them locally reduces security risks and prevents unauthorized access.

4. **Dynamic User Interface**: Displaying bank cards dynamically based on API data with proper masking of sensitive information (showing only last 4 digits of card numbers) balances usability with security. Including bank names and card holder information improves user confidence in the payment process.

5. **Context Preservation**: Using both server-side session storage (`active_payments` dictionary) and client-side context (`context.user_data`) provides redundancy for critical transaction data. If one mechanism fails, the other can often recover the session information, improving reliability.

6. **Asynchronous Error Handling**: Financial operations require comprehensive error handling with user-friendly messages. Using try-except blocks around API calls with detailed error logging and user-appropriate messages maintains a good user experience while providing debugging information for developers.

7. **Clean Cancellation Paths**: Providing clear cancellation options at every step of the payment process improves user experience and prevents frustration. The implementation allows users to cancel payments at any point with proper cleanup of both UI elements and backend session data.

8. **Payment Proof Validation**: Implementing multi-stage validation (image format, reference number length) prevents invalid submissions from reaching the API. This validation cascade improves system efficiency by failing fast on invalid inputs.

9. **Graceful Degradation**: Designing the system to handle API failures gracefully with retry options ensures that temporary backend issues don't permanently block users from completing payments. The implementation includes options to retry submissions and clear error messages explaining what went wrong.

10. **Task Isolation**: Creating dedicated modules for payment handling (`payment_proof_handlers.py`) with clear interfaces to other components (like `buy_flow.py`) improves maintainability. This separation of concerns makes the codebase easier to understand, test, and modify.

These lessons illustrate how financial transaction flows in conversational interfaces require careful attention to state management, security, and user experience considerations beyond typical bot development patterns.

## Payment Admin Performance Reporting System Implementation (July 2024)

### Lessons Learned:
1. **Metric Design for Performance Evaluation**: Creating a comprehensive metrics system for admin performance required balancing quantitative measures (approval rates, response times) with qualitative insights (rejection reasons, bank card distribution). The implementation demonstrates how combining these metrics provides a more complete picture of performance than any single measure alone.

2. **Data Aggregation Efficiency**: When building reporting systems that analyze large datasets, efficient data aggregation is critical. The implementation uses SQL's aggregate functions where possible (for counts and simple metrics) combined with Python post-processing for more complex calculations, striking a balance between query optimization and code maintainability.

3. **Visualization in Telegram Context**: Implementing data visualization in a Telegram bot context presented unique challenges. Using matplotlib with BytesIO streams allowed for dynamic chart generation without filesystem dependencies, making the application more containerizable and deployment-friendly while providing rich visualizations.

4. **Flexible Date Range Filtering**: Implementing preset date ranges (today, week, month, all time) with dynamic calculation makes reports more accessible to users than requiring manual date input. The implementation handles cultural calendar differences by calculating week start based on Saturday (Iranian calendar) rather than Monday, demonstrating awareness of regional variations.

5. **Text Formatting for Mobile Readability**: Creating text-based reports that remain readable on mobile devices required careful attention to formatting. Using emoji indicators, proper spacing, and a clear visual hierarchy ensured that reports maintain their meaning even without accompanying charts, important for users on various device types.

6. **Admin Self-Assessment Tools**: Providing individual admins with detailed metrics about their own performance creates transparency and encourages improvement. The "My Performance" report section gives each admin visibility into their metrics without requiring superuser access to system-wide reports.

7. **API Parameter Flexibility**: Designing reporting endpoints with optional parameters (start_date, end_date, admin_id) creates a flexible API that serves multiple use cases. The same endpoint supports both individual admin performance reviews and system-wide analytics, reducing API complexity while maximizing utility.

8. **Chart Data Selection Strategy**: When visualizing performance data, displaying all metrics would create overcrowded, unreadable charts. The implementation focuses on three key comparative metrics (approval rate, transaction count, response time) and limits display to the top 5 admins by volume, making charts informative without overwhelming users.

9. **Report Caching Considerations**: Performance reports can be resource-intensive to generate. While the current implementation generates reports on-demand, future versions might benefit from implementing a caching layer that refreshes reports on a schedule, reducing database load during peak usage times.

10. **Progressive Detail Disclosure**: The reporting UI follows a progressive disclosure pattern, showing high-level metrics first and allowing users to drill down into specific date ranges or individual admin details. This approach prevents information overload while still providing access to comprehensive data.

These lessons highlight the importance of thoughtful design in reporting systems, balancing technical performance with user experience considerations to create tools that drive operational improvements through data-driven insights.

## Payment Notification System Implementation (July 2024)

### Lessons Learned:
1. **Card-Specific Admin Assignment**: Creating a mapping system between bank cards and specific admin groups allows for specialized payment verification workflows. The implementation demonstrates how assigning specific admins to particular cards creates clear responsibility boundaries and improves response times through domain expertise (admins familiar with specific banks).

2. **Message Tracking Between Systems**: When implementing notification systems that span multiple services (bot, API, database), tracking message IDs is critical for maintaining state. The implementation uses a database field to store Telegram message IDs and group IDs, enabling future message updates and preventing duplicate notifications.

3. **Multi-Stage Rejection Workflows**: Implementing a staged rejection workflow (reject button → reason selection → confirmation) prevents accidental rejections and captures valuable rejection reasons. The implementation uses a two-step process with predefined common reasons and custom reason option, balancing speed with flexibility.

4. **Bidirectional Notification**: Creating a notification system that informs both admins (about new payments) and users (about verification outcomes) closes the communication loop. The implementation sends detailed notifications to users upon approval/rejection, including subscription details or specific rejection reasons, enhancing transparency.

5. **Permissions Layering**: Implementing multiple permission checks (API level and bot level) provides defense in depth against unauthorized actions. The implementation validates permissions in both the API endpoints and Telegram handlers, ensuring only authorized admins can approve or reject payments even if one layer is compromised.

6. **Card Number Security**: When displaying card information, implementing proper masking (showing only first/last 4 digits) is critical for security. The implementation uses regex to standardize and mask card numbers, preventing accidental exposure of full card details while maintaining usability.

7. **Function Specialization**: Separating notification generation from notification sending enables better testability and module reuse. The implementation separates message formatting, permission checking, and API communication into distinct functions with single responsibilities, improving maintainability.

8. **Error Resilience in Financial Workflows**: Implementing comprehensive error handling ensures financial operations don't leave users in ambiguous states. The error handling approach includes fallback paths, explicit error messages, and transaction isolation to prevent half-completed operations.

9. **Contextual Information Enhancement**: Including relevant context in notifications (order details, payment amount, timestamps) improves decision quality for admins. The implementation gathers data from multiple sources (order, user, card) to present a complete picture for verification decisions.

10. **API Endpoint Specialization**: Creating specialized endpoints for specific functions (like updating Telegram message IDs) improves API clarity compared to generic update endpoints. The implementation uses dedicated endpoints with clear naming and purpose rather than overloading general update methods.

These lessons highlight the importance of clear responsibility boundaries, secure communication, and user feedback loops in financial verification systems.
