# Tez Mobile App — Complete UI/UX System Specification

## 1) App Purpose
Execution-first mobile experience focused on:
1. Approvals
2. Chat
3. Notifications

Product qualities:
- Fast, low-friction interaction
- Premium enterprise visual tone
- Security-forward without heavy cognitive load
- Strong actionability for managers and approvers on the move

---

## 2) Design Language
### Theme foundation (Dark Premium)
- App background: `#0B0D10` (near-black)
- Elevated surface: `#13171C`
- Card surface: `#171C22`
- Primary text: `#F5F7FA`
- Secondary text: `#9AA4B2`
- Divider: `#2A313B`

### Semantic colors
- Critical / mandatory / destructive: `#E5484D`
- Informational / links / active controls: `#3B82F6`
- Premium accent (subtle): `#C8A96B`
- Success: `#22C55E`
- Warning: `#F59E0B`

### Style rules
- Rounded corners: 10–14px on cards and sheets
- Touch targets: min 44x44pt
- Icon usage: supportive, not decorative overload
- Shadow: minimal; rely on contrast and layering

### Typography scale (enterprise sans-serif)
- Display: 28/34, weight 700
- Title: 22/28, weight 700
- Section: 18/24, weight 600
- Body: 15/22, weight 400/500
- Caption/meta: 12/16, weight 500

---

## 3) App-wide UX Principles
- One-hand optimized: key actions in thumb zone.
- Minimum taps for critical operations (approve/reject/reply).
- Sticky headers and sticky action bars on long screens.
- Pull-to-refresh on list screens.
- Swipe actions where high-value (mark read, quick approve optional).
- Strong explicit states: loading, empty, error, offline, success.
- Bottom sheets for transient decisions (reject reason, filters, quick actions).
- No dead ends: every state has a next action.

---

## 4) Information Architecture
## A) Auth
- Splash
- Login
- PIN Setup
- Biometric Setup
- App Lock (re-auth)

## B) Home
- Summary Dashboard
- Today View (agenda)
- Quick Actions

## C) Approvals
- Approval Inbox
- Approval Detail
- Reject Reason Modal / Send Back Modal
- Related Item Detail (Task / Job / Project)

## D) Chat
- Chat Home
- DMs
- Channels
- Conversation
- Thread
- Chat Info (members/files/context)

## E) Notifications
- Notification Center
- Notification Redirect Resolver (internal routing layer)
- Notification Preferences

## F) Settings
- Account
- Security
- Notification Settings
- About / Version
- Logout

---

## 5) Navigation Model
## Primary shell
- Bottom Tabs:
  1. Home
  2. Approvals
  3. Chat
  4. Notifications
  5. Settings

## Secondary navigation
- Stack navigation per tab for detail drill-down.
- Modal stack for sheets/actions (filters, reject reason, quick action).

## Badging and deep links
- Dynamic badge counts on Approvals/Chat/Notifications.
- Deep links:
  - `tez://approvals/:id`
  - `tez://chat/channel/:id`
  - `tez://chat/dm/:id`
  - `tez://notifications/:id`
- Push notification taps route to exact detail screen.

---

## 6) Complete Screen Map + Purpose
## AUTH
1. `SplashScreen` — bootstrap auth/session/config checks.
2. `LoginScreen` — email/password, SSO-ready slot.
3. `PinSetupScreen` — create 4/6-digit PIN.
4. `BiometricSetupScreen` — opt-in biometric unlock.
5. `AppLockScreen` — lock on resume/session timeout.

## HOME
6. `HomeDashboardScreen` — approval/chat/notification summary cards.
7. `TodayAgendaScreen` — today’s items and deadlines.
8. `QuickActionSheet` — jump actions (approve next, open unread chats, high-priority alerts).

## APPROVALS
9. `ApprovalInboxScreen` — segmented statuses + filters + search.
10. `ApprovalDetailScreen` — summary, trail, related item preview, action bar.
11. `RejectReasonModal` — mandatory reason capture for Reject/Send Back.
12. `RelatedTaskDetailScreen` — read-only full task context.
13. `RelatedJobDetailScreen` — read-only full job context.
14. `RelatedProjectDetailScreen` — read-only full project context.

## CHAT
15. `ChatHomeScreen` — DM/Channel segmented recents.
16. `DMListScreen` — direct message index.
17. `ChannelListScreen` — channels index with unread counts.
18. `ChatConversationScreen` — threaded-capable conversation.
19. `ThreadScreen` — focused reply thread.
20. `ChatInfoScreen` — members, files, linked context.
21. `AttachmentPreviewScreen` — image/pdf/doc preview.

## NOTIFICATIONS
22. `NotificationCenterScreen` — grouped feed, filters, read actions.
23. `NotificationPreferencesScreen` — push/category controls.

## SETTINGS
24. `SettingsHomeScreen` — settings hub.
25. `AccountScreen` — profile/session/logout.
26. `SecuritySettingsScreen` — biometrics/PIN/relock.
27. `NotificationSettingsScreen` — granular notification controls.
28. `AboutScreen` — version/build/support.

---

## 7) Home Dashboard UX
Layout blocks (top-to-bottom):
1. Greeting + status chip (online/offline sync)
2. KPI row (pending approvals, unread chats, critical alerts)
3. Today agenda timeline
4. Quick actions strip
5. High-priority cards (SLA/approval overdue)

Behavior:
- Tapping KPI opens filtered module list.
- Pull to refresh refreshes all counts.
- Quick actions open directly to actionable screens.

---

## 8) Approvals UX
## Inbox
- Segmented control: Pending / Approved / Rejected / Sent Back
- Search by reference/name
- Filter sheet: module, date range, pending level, project, priority
- Card fields: module, reference ID, creator, context name, level, SLA badge, created date

## Detail
- Sticky header with status and SLA
- Approval summary card
- Approval trail timeline (L1→L2 etc.)
- Related item preview block
- CTA: `View Full Details`
- Sticky bottom actions: `Approve`, `Reject`, `Send Back`

## Reject/Send Back
- Opens bottom sheet modal
- Mandatory multiline reason
- Reject button disabled until non-whitespace reason
- Confirmation toast and history update callback

---

## 9) Chat UX
## Chat Home
- Segmented DMs / Channels
- Search bar + unread filter chip
- Unread count badges + latest message preview

## Conversation
- Sticky top bar with avatar/name/channel
- Message list with date separators
- Bubble styles: own vs others
- Read states + delivery indicator slots
- Typing indicator row reserved
- Composer fixed bottom: text + attachment + send

## Thread
- Parent message pinned
- Replies list and dedicated composer

## Chat Info
- Members list
- Shared files
- Linked project/task context

---

## 10) Notification UX
- Group by date sections (Today, Yesterday, Earlier)
- Unread visual emphasis
- Priority chips (High/Medium/Low)
- Actions: mark read, mark all read, filter by type
- Tap behavior routes to exact approval/chat/context screen

---

## 11) Settings UX
## Account
- user info, org scope, app version, logout

## Security
- biometric toggle
- change PIN
- app relock timer
- session controls

## Notifications
- push master toggle
- category toggles (approvals/chat/system)
- summary cadence

---

## 12) Design System Component Inventory
Each component includes purpose, variants, states, spacing, interactions.

1. `AppShell`
- Purpose: safe-area scaffold + status bar style
- Variants: standard / modal
- States: default
- Spacing: outer 16px
- Interaction: owns scroll container boundaries

2. `TopHeader`
- Variants: title-only / title+search / title+actions
- States: default, compact(scrolled)

3. `BottomTabBar`
- Variants: with badges / without badges
- States: active/inactive

4. `SearchBar`
- States: idle/focus/loading/no-results

5. `SegmentedControl`
- Used in Approvals and Chat
- States: selected/disabled

6. `ListRow`
- Variants: simple/detailed/with trailing action

7. `ApprovalCard`
- Variants: pending/approved/rejected/sent-back
- Includes SLA and priority indicators

8. `NotificationCard`
- Variants: unread/read/high-priority

9. `ChatListItem`
- Variants: DM/channel
- Shows unread badge and typing snippet if available

10. `MessageBubble`
- Variants: self/other/system
- States: sent/delivered/read/failed

11. `ContextChip / StatusChip`
- semantic color mapping

12. `PriorityBadge`
- high/medium/low

13. `EmptyState`
- icon + message + CTA

14. `ErrorState`
- retry action

15. `SkeletonLoader`
- list/card/detail variants

16. `BottomSheet`
- for filters and reject reason

17. `Modal`
- for blocking confirmations

18. `CTA Button`
- primary action

19. `Secondary Button`
- neutral action

20. `Danger Button`
- destructive actions (Reject/Send Back)

21. `Secure PIN Keypad`
- numeric only, masked input

22. `BiometricPrompt`
- trust-oriented branded prompt card

23. `AttachmentTile`
- file icon/type/size with open/download

24. `FilterChipRow`
- horizontal scroller for active filters

Spacing rule set:
- 4pt micro
- 8pt compact
- 12pt default
- 16pt section
- 24pt block

---

## 13) Mobile Security UX Flows
1. Login success -> PIN setup required.
2. PIN setup success -> biometric opt-in prompt.
3. App relock after inactivity -> AppLock screen (PIN/biometric).
4. Session expired -> clear explanation + relogin CTA.
5. Sensitive actions (Reject/Send Back optional re-auth) if policy enabled.

Tone: concise, clear, trusted, no technical jargon in user copy.

---

## 14) iOS + Android Adaptation Notes
- SafeArea handling for notches and dynamic island.
- Keyboard avoiding for composer and forms.
- iOS: gesture back and haptic subtle taps.
- Android: hardware back behavior with exit confirmation on root tabs.
- Tab bar hit areas >=44pt.
- Sheet behavior tuned per platform velocity and snap points.

---

## 15) Required States per Screen
Every screen must define:
- Default
- Loading (skeletons)
- Empty
- Error (retry)
- Offline (cached + sync notice)
- Success confirmation (toast/snackbar)

---

## 16) Final Mobile UX Architecture Summary
- Navigation: bottom tab + per-tab stacks + modal/sheet actions.
- Core loop: Home glance -> Approvals decisions -> Chat collaboration -> Notification triage.
- Security loop: secure login -> app lock -> quick re-auth.
- Design system: compact, dark-premium, high-contrast, reusable components.
- Delivery focus: approvals/chat/notifications are first-class, high-velocity workflows.

---

## 17) Global Header + Contextual Help Parity
For web + mobile parity, every major screen should expose:
- Product context in header (tenant/company + FY)
- Quick actions (+)
- Help (?) opening right-side/context sheet
- Notification bell with unread count
- Profile actions (profile/settings/security/logout)

Contextual help content is keyed by `screen_key` and rendered from backend help API, not hardcoded copy.
