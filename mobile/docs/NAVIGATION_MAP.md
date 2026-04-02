# Tez Mobile Navigation Map

## Root
- AuthStack (unauthenticated)
- MainTabs (authenticated)
- LockScreenOverlay (session timeout/re-auth)

## AuthStack
- SplashScreen
- LoginScreen
- PinSetupScreen
- BiometricSetupScreen

## MainTabs
1. HomeTab
   - HomeDashboardScreen
   - TodayAgendaScreen
   - QuickActionSheet (modal)
2. ApprovalsTab
   - ApprovalInboxScreen
   - ApprovalDetailScreen
   - RelatedTaskDetailScreen
   - RelatedJobDetailScreen
   - RelatedProjectDetailScreen
   - RejectReasonModal (sheet/modal)
3. ChatTab
   - ChatHomeScreen
   - DMListScreen
   - ChannelListScreen
   - ChatConversationScreen
   - ThreadScreen
   - ChatInfoScreen
   - AttachmentPreviewScreen
4. NotificationsTab
   - NotificationCenterScreen
   - NotificationPreferencesScreen
5. SettingsTab
   - SettingsHomeScreen
   - AccountScreen
   - SecuritySettingsScreen
   - NotificationSettingsScreen
   - AboutScreen

## Deep Links
- `tez://approvals/:approvalId`
- `tez://chat/channel/:channelId`
- `tez://chat/dm/:dmId`
- `tez://chat/thread/:threadId`
- `tez://notifications/:notificationId`

## Badge Sources
- Approvals tab badge: pending approvals count
- Chat tab badge: unread messages/mentions count
- Notifications tab badge: unread notification count
