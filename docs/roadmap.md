# Roadmap
This section outlines the future plans and enhancements for the project. It provides an overview of the features and improvements that are currently missing and planned for implementation.

## Feature Enhancements

1. Notifications
   - Implement different types of notifications, not limited to mobile devices.
   - Provide e.g. email and push notification options for users.

2. Mobile App:
   - Develop a dedicated mobile application to enhance user accessibility and convenience.

3. Optimization:
   - Optimize sync speed to handle the continuous growth of the beacon chain efficiently.

4. Enhanced User Interface:
   - Display deposits and validators before they are processed by the beacon chain.
   - Improve the single slot view by adding missing information.
   - Add slots table to the epoch view.
   - Show the pool association for each validator.
   
5. API Enhancements:
   - Expand the existing API to include additional endpoints and functionalities.
   - Provide comprehensive API documentation for developers to easily integrate with the project.

6. Multi-Chain Support:
   - Connect accounts and notifications across different chains, allowing users to easier monitor across multiple chains.

## Backend and Infrastructure
1. Performance Improvements:
   - Optimize server response time for a large number of validators.
   - Tests show that with a few optimizations, 2000 validators should be easily doable but needs a better frontend.
   - From ~2000 validators on, the server response time increases linearly. e.g., 2000 need 0.12 seconds, but 20000 need 1.2 seconds, which is far too long to allow anyone to add that many
   - Allow individual users to exceed the maximum validator limit, considering performance implications.
   
2. Separate Beacon API Package:
   - Extract and create a separate package for the beacon API
   - Web3.py beacon can't be used because of many missing functions and the hardcoded timeout.

## User Experience and Usability
1. Styling and Responsiveness:
   - Improve overall styling, with particular focus on mobile devices.
   - Enhance the user experience by making the interface more intuitive and user-friendly.
   
2. Exporting Staking Rewards:
   - Provide options to export staking rewards as CSV, JSON, or other commonly used formats.
   
3. Dashboard Enhancements:
   - Include pending validators in the dashboard, along with the time it takes for them to go online.
   - Allow the addition of validators to the dashboard before they are processed by the beacon chain.
   - Enable automatic addition of validators with the same withdrawal address.
   - List current eth client (beacon, execution, and mev) versions.
   
## Other Improvements
1. MEV Boost Information:
   - Display statistics on the number of blocks utilizing MEV boost, utilizing existing database information.

2. Password Reset:
   - Add password reset functionality for user accounts.

3. Testing and Quality Assurance:
   - Develop comprehensive test cases to prevent regressions and ensure stability.
   
4. Production setup guide
