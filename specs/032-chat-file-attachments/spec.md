# Feature Specification: Copy/Paste Image & File Attachments to App Chat with GitHub Parent Issue Integration

**Feature Branch**: `032-chat-file-attachments`  
**Created**: 2026-03-09  
**Status**: Draft  
**Input**: User description: "Allow the user to copy/paste images/files into the app chat - add it as a chat attachment. When a user is attempting to create a new GitHub Parent Issue via app chat with attachments included in the message. Attach these chat attachments to the GitHub Parent Issue as file attachments."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Paste Image into Chat (Priority: P1)

As a user composing a chat message, I want to paste an image from my clipboard directly into the chat input area so that I can quickly share visual context (screenshots, diagrams, photos) without leaving the chat workflow.

**Why this priority**: Clipboard paste is the most common and fastest method users employ to share images. This is the core interaction that enables all downstream attachment features and delivers immediate, standalone value.

**Independent Test**: Can be fully tested by copying an image to the clipboard and pressing Ctrl+V / Cmd+V in the chat input. The image appears as an inline thumbnail preview before sending, and the user can remove it before submission.

**Acceptance Scenarios**:

1. **Given** the user has an image copied to the clipboard (PNG, JPEG, GIF, or WebP), **When** the user presses Ctrl+V / Cmd+V while the chat input is focused, **Then** the image appears as a thumbnail preview in the attachment area above or below the text input.
2. **Given** an image preview is displayed in the attachment area, **When** the user clicks the dismiss (✕) button on the preview, **Then** the image is removed from the pending attachments and the preview disappears.
3. **Given** the user has pasted an image and typed a text message, **When** the user sends the message, **Then** both the text and the attached image are included in the sent chat message, and the attachment preview is cleared from the input area.
4. **Given** the user pastes plain text from the clipboard, **When** the paste event fires, **Then** the system inserts the text normally and does not create an attachment preview.

---

### User Story 2 - Attach Files to GitHub Parent Issue on Creation (Priority: P1)

As a user creating a new GitHub Parent Issue via the app chat, I want all images and files I attached to my chat message to be automatically uploaded and linked as file attachments on the newly created GitHub issue, so that my issue contains all relevant supporting materials without requiring me to manually re-upload them on GitHub.

**Why this priority**: This is the primary integration value — bridging chat attachments to GitHub issues. Without this, attachments remain isolated in the chat and the user must duplicate effort on GitHub.

**Independent Test**: Can be fully tested by attaching one or more files to a chat message, triggering GitHub Parent Issue creation, and verifying that all attachments appear as linked files on the created GitHub issue.

**Acceptance Scenarios**:

1. **Given** a chat message contains one or more attachments and the message triggers GitHub Parent Issue creation, **When** the issue is successfully created, **Then** all attached files are uploaded and linked as file attachments on the GitHub issue.
2. **Given** the GitHub Parent Issue was created with attachments, **When** creation is complete, **Then** the chat displays a confirmation message indicating success along with the number of attachments included (e.g., "Issue created with 2 attachments").
3. **Given** a chat message triggers issue creation but one attachment fails to upload (e.g., network error), **When** the issue is created, **Then** the issue is still created with successfully uploaded attachments, and the user is notified about which attachment(s) failed.

---

### User Story 3 - Drag-and-Drop Files into Chat (Priority: P2)

As a user, I want to drag and drop images or files from my desktop or file explorer directly onto the chat input area so that I can attach files without needing to copy them to the clipboard first.

**Why this priority**: Drag-and-drop is a widely expected alternative attachment method that complements clipboard paste. It supports bulk file operations and non-image file types more naturally than clipboard paste.

**Independent Test**: Can be fully tested by dragging one or more files from the desktop onto the chat input area. Each file appears as a preview (thumbnail for images, file chip for non-images) in the attachment area.

**Acceptance Scenarios**:

1. **Given** the user drags one or more files over the chat input area, **When** the files are within the drop zone, **Then** the chat input area displays a visual drop indicator (e.g., highlighted border or overlay) to signal that dropping is supported.
2. **Given** the user drops supported files onto the chat input, **When** the drop event fires, **Then** each file is added to the pending attachments with an appropriate preview (thumbnail for images, file chip with name and size for non-images).
3. **Given** the user drops a mix of supported and unsupported file types, **When** the drop event fires, **Then** supported files are added as attachments and unsupported files trigger inline error messages without blocking the valid attachments.

---

### User Story 4 - Manual File Picker as Fallback (Priority: P2)

As a user, I want to click an attachment icon/button in the chat toolbar to browse and select files from my device so that I have an accessible, discoverable fallback when clipboard paste or drag-and-drop is inconvenient or unsupported.

**Why this priority**: A manual file picker ensures accessibility for all users and provides discoverability for the attachment feature. Some users may not be familiar with paste or drag-and-drop workflows.

**Independent Test**: Can be fully tested by clicking the attachment icon in the chat toolbar, selecting files from the native file browser, and verifying they appear as attachment previews in the chat input area.

**Acceptance Scenarios**:

1. **Given** the chat input toolbar is visible, **When** the user looks at the toolbar, **Then** an attachment icon/button is visible and clearly indicates its purpose.
2. **Given** the user clicks the attachment icon, **When** the file browser opens, **Then** the user can select one or more files, and selected files appear as previews in the attachment area.
3. **Given** the user selects a file that exceeds the 10 MB size limit, **When** the file is selected, **Then** an inline warning is displayed for the oversized file and it is not added to the pending attachments, while any valid files from the same selection are still added.

---

### User Story 5 - Attachment Validation and Error Handling (Priority: P2)

As a user, I want to receive clear, non-blocking feedback when I attempt to attach an unsupported file type or a file that exceeds size limits so that I can correct the issue without losing my message text or other valid attachments.

**Why this priority**: Robust error handling prevents user frustration and data loss. Inline, non-blocking errors ensure the chat input remains usable even when individual attachments are rejected.

**Independent Test**: Can be fully tested by attempting to attach files of unsupported types and files exceeding 10 MB, and verifying that appropriate inline errors appear without disrupting the text input or other valid attachments.

**Acceptance Scenarios**:

1. **Given** the user attempts to attach a file that exceeds 10 MB, **When** the file is added via any method (paste, drop, or file picker), **Then** an inline error message is displayed (e.g., "File exceeds 10 MB limit") and the file is not added to the pending attachments.
2. **Given** the user attempts to attach an unsupported file type, **When** the file is added via any method, **Then** an inline error message is displayed (e.g., "Unsupported file type: .exe") and the file is not added.
3. **Given** the user has valid attachments and types a message, **When** a subsequent attachment is rejected due to validation, **Then** the existing message text and valid attachments remain intact and unaffected.

---

### Edge Cases

- What happens when the user pastes content that contains both text and an image (e.g., from a rich text editor)? The system should extract and attach the image separately while inserting the text as message content.
- What happens when the user attaches multiple files that collectively exceed a reasonable total size (e.g., 25 MB across all attachments)? The system should enforce per-file limits (10 MB each) and allow up to 10 attachments per message; excess files are rejected with an inline message.
- What happens when the user loses network connectivity mid-upload during GitHub issue creation? The system should retry failed uploads once, then notify the user of the specific failed attachment(s) while still creating the issue with successful uploads.
- What happens when the user edits the message text after attaching files but before sending? All attachment previews should remain visible and associated with the message.
- What happens when the user navigates away from the chat input before sending? Pending attachments should be cleared to free memory resources; a confirmation prompt should appear if attachments are present.
- What happens when the user pastes a very large image (e.g., a high-resolution screenshot over 10 MB)? The system should validate the size after paste and display an inline error if it exceeds the limit.
- What happens when the GitHub API rate limit is exceeded during attachment upload? The system should queue remaining uploads and retry after the rate limit window resets, or notify the user to try again later.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST intercept clipboard paste events in the chat input to detect and capture pasted images (PNG, JPEG, GIF, WebP) and files of common types (PDF, ZIP, TXT, CSV, MD, DOCX, XLSX, JSON, YAML, SVG, BMP)
- **FR-002**: System MUST display an inline thumbnail preview for each attached image and a file chip (showing filename and file size) for each non-image attachment, rendered in the chat input area before message submission
- **FR-003**: System MUST allow users to remove any individual attachment from the pending list before sending via a clearly visible dismiss (✕) control on each preview
- **FR-004**: System MUST support drag-and-drop of files and images onto the chat input area as an alternative attachment method, with a visual drop zone indicator when files are dragged over the target area
- **FR-005**: System MUST provide a manual file picker (attachment icon/button in chat toolbar) as a fallback attachment method for accessibility and discoverability
- **FR-006**: System MUST upload all chat attachments and link them as file attachments on the newly created GitHub Parent Issue when issue creation is triggered from a chat message
- **FR-007**: System MUST display a confirmation message in the chat indicating the GitHub Parent Issue was created successfully along with the count of attachments included (e.g., "Issue created with 2 attachments")
- **FR-008**: System MUST validate each attachment against supported file types and a per-file size limit of 10 MB, displaying an inline error for rejected files without blocking valid attachments or the text input
- **FR-009**: System MUST support up to 10 simultaneous attachments in a single message/issue creation event
- **FR-010**: System SHOULD preserve attachment previews if the user edits their message text before sending, and clear all previews after the message is successfully submitted
- **FR-011**: System SHOULD release memory resources for attachment previews when the chat input component is unmounted or the user navigates away
- **FR-012**: System MUST gracefully handle partial upload failures during GitHub issue creation — the issue should still be created with successfully uploaded attachments, and the user should be notified of any failed uploads

### Key Entities

- **Chat Attachment**: Represents a file pending submission with the chat message. Key attributes: file reference, file name, file size, file type (MIME type), preview (thumbnail URL for images), validation status (valid, rejected with reason), upload state (pending, uploading, uploaded, failed)
- **Attachment Preview**: The visual representation of a pending attachment in the chat input area. Types: image thumbnail (for image files) and file chip (for non-image files showing name and size). Each preview includes a dismiss control
- **GitHub Issue Attachment**: A file uploaded and linked to a GitHub Parent Issue. Key attributes: source chat attachment reference, upload URL, GitHub asset reference, upload status

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can attach an image via clipboard paste in under 2 seconds from pressing Ctrl+V / Cmd+V to seeing the thumbnail preview
- **SC-002**: Users can attach files via drag-and-drop with a visible drop zone indicator appearing within 200 milliseconds of dragging files over the chat area
- **SC-003**: 100% of supported file types (PNG, JPEG, GIF, WebP, PDF, ZIP, TXT, CSV, MD, DOCX, XLSX, JSON, YAML, SVG, BMP) are correctly detected and accepted for attachment
- **SC-004**: Files exceeding 10 MB are rejected with an inline error within 1 second of the user attempting to attach them, without disrupting existing message text or valid attachments
- **SC-005**: When a GitHub Parent Issue is created with attachments, 100% of successfully uploaded attachments are accessible and viewable on the GitHub issue page
- **SC-006**: Users receive a confirmation message (including attachment count) within 5 seconds of triggering GitHub Parent Issue creation for messages with up to 5 attachments
- **SC-007**: 95% of users can successfully attach and send at least one file on their first attempt without requiring help documentation

### Assumptions

- Users have an authenticated session with sufficient permissions (repository write access) for GitHub issue creation and file upload
- The app chat already supports creating GitHub Parent Issues from chat messages; this feature extends that existing workflow with attachment capabilities
- GitHub's file attachment size limit of 10 MB per file is the governing constraint for individual file size validation
- The maximum number of attachments per message is set to 10 to balance usability with performance
- Supported file types are based on common document and image formats; executable files (.exe, .bat, .sh, .msi) are excluded for security reasons
- The chat input component already exists and this feature adds attachment capabilities to it
- Network connectivity is generally reliable; retry logic handles transient failures but does not queue uploads for extended offline periods
