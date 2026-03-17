# Feature Specification: Transcript Upload & Transcribe Agent

**Feature Branch**: `049-transcript-upload-transcribe`  
**Created**: 2026-03-17  
**Status**: Draft  
**Input**: User description: "Add transcript file upload support to both Chat and Parent Issue Intake. When a transcript file (.txt/.md with content detection, .vtt, .srt) is detected, automatically route it through a new Transcribe agent that extracts user requirements/user stories from multi-speaker meeting conversations. The agent outputs a structured IssueRecommendation that creates a GitHub Parent Issue with a requirements outline and sub-issues via the selected Agent Pipeline."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Upload Transcript in Chat to Generate Requirements (Priority: P1)

A project manager has just finished a stakeholder meeting and has a transcript file. They open the Chat interface, upload the transcript file, and the system automatically detects it as a meeting transcript. Without any additional prompts, the system analyzes the conversation, extracts user requirements and user stories, and presents a structured issue recommendation. The project manager reviews the extracted requirements and confirms to create a GitHub Parent Issue with sub-issues via their selected Agent Pipeline.

**Why this priority**: This is the core value proposition of the feature — transforming unstructured meeting conversations into actionable, structured project requirements. The Chat interface is the primary interaction point for users and provides immediate, interactive feedback.

**Independent Test**: Can be fully tested by uploading a `.vtt` or `.srt` transcript file in Chat and verifying that an issue recommendation preview appears with extracted requirements. Delivers immediate value by eliminating manual requirement extraction from meeting transcripts.

**Acceptance Scenarios**:

1. **Given** a user is in a Chat session with a project, **When** they upload a `.vtt` file containing a multi-speaker meeting transcript, **Then** the system detects it as a transcript, analyzes the conversation, and displays an issue recommendation preview with a title, user stories, and functional requirements extracted from the discussion.
2. **Given** a user is in a Chat session and an issue recommendation preview is displayed from a transcript, **When** they confirm the recommendation, **Then** a GitHub Parent Issue is created with the extracted requirements in the body and sub-issues are generated via the selected Agent Pipeline.
3. **Given** a user is in a Chat session, **When** they upload an `.srt` subtitle file containing a meeting transcript, **Then** the system detects it as a transcript and processes it identically to a `.vtt` file.

---

### User Story 2 - Upload Transcript via Parent Issue Intake (Priority: P2)

A team lead wants to create a new project initiative based on a planning meeting. They navigate to the Parent Issue Intake panel, upload a transcript file (or paste transcript content directly), select their desired Agent Pipeline, and submit. The system detects the transcript content, extracts structured requirements, and uses the generated title and formatted requirements body to create the GitHub Parent Issue with sub-issues.

**Why this priority**: The Parent Issue Intake is a secondary but important entry point for creating structured issues. Supporting transcripts here ensures users have a consistent experience regardless of which workflow they use.

**Independent Test**: Can be fully tested by uploading a speaker-labeled `.txt` file in the Parent Issue Intake panel, selecting a pipeline, and verifying that the created GitHub issue contains extracted requirements rather than raw transcript text.

**Acceptance Scenarios**:

1. **Given** a user is on the Parent Issue Intake panel, **When** they upload a `.txt` file containing speaker-labeled meeting notes (e.g., lines like "Alice: We need a dashboard for analytics"), **Then** the system detects it as a transcript, extracts requirements, and uses the structured output as the issue body.
2. **Given** a user is on the Parent Issue Intake panel, **When** they paste transcript content directly into the description field and submit, **Then** the system detects the transcript patterns in the text, processes it through the Transcribe agent, and creates the issue with structured requirements.
3. **Given** a user is on the Parent Issue Intake panel, **When** they upload a `.vtt` or `.srt` file, **Then** the file is accepted by the file picker and processed as a transcript.

---

### User Story 3 - Non-Transcript Files Pass Through Normally (Priority: P2)

A developer uploads a regular `.txt` file (plain notes, code snippets, or documentation) via Chat or Parent Issue Intake. The system examines the content, determines it is not a meeting transcript, and routes it through the existing normal processing flow (feature-request detection, etc.) without any disruption to the current experience.

**Why this priority**: Preserving backward compatibility is essential. The transcript detection must not interfere with existing workflows for non-transcript files. This shares P2 priority because it is critical for user trust.

**Independent Test**: Can be fully tested by uploading a plain `.txt` file with regular notes (no speaker labels or timestamps) and verifying that the existing behavior (feature-request detection or normal chat response) is unchanged.

**Acceptance Scenarios**:

1. **Given** a user is in a Chat session, **When** they upload a `.txt` file containing plain prose (no speaker labels, no timestamps), **Then** the system does not treat it as a transcript and processes it through the existing feature-request detection or normal chat flow.
2. **Given** a user is in a Chat session, **When** they upload a `.md` file containing standard markdown documentation, **Then** the system does not treat it as a transcript and processes it normally.
3. **Given** a user is on the Parent Issue Intake panel, **When** they type a plain text description (not a transcript) and submit, **Then** the existing behavior is unchanged — no transcript processing occurs.

---

### User Story 4 - Transcript Format Detection Across File Types (Priority: P3)

The system supports multiple transcript formats and intelligently detects transcripts even when the file extension is ambiguous. Files with `.vtt` and `.srt` extensions are always treated as transcripts. Files with `.txt` or `.md` extensions are analyzed for transcript patterns: speaker labels (e.g., "John:", "Speaker 1:", "[Jane]:"), timestamps (e.g., "00:01:23"), or structural markers (e.g., "WEBVTT", "-->"). This ensures broad compatibility with transcripts from various meeting tools and manual note-taking styles.

**Why this priority**: While the core upload-and-process flow (P1/P2) delivers the main value, robust detection across file types ensures the feature works reliably with transcripts from different sources. This is important for user confidence but is less critical than the primary flows.

**Independent Test**: Can be tested by uploading a set of diverse transcript files (`.vtt`, `.srt`, speaker-labeled `.txt`, timestamped `.txt`) and verifying each is correctly detected, as well as confirming that non-transcript `.txt` and `.md` files are not falsely detected.

**Acceptance Scenarios**:

1. **Given** any file with a `.vtt` extension, **When** it is uploaded or its content is analyzed, **Then** it is always classified as a transcript regardless of content.
2. **Given** any file with a `.srt` extension, **When** it is uploaded or its content is analyzed, **Then** it is always classified as a transcript regardless of content.
3. **Given** a `.txt` file containing 3 or more lines with speaker labels (e.g., "Alice: ...", "Bob: ..."), **When** it is analyzed, **Then** it is classified as a transcript.
4. **Given** a `.txt` file containing 5 or more lines with timestamps (e.g., "00:01:23 ...", "1:45:00 ..."), **When** it is analyzed, **Then** it is classified as a transcript.
5. **Given** a `.md` file containing standard markdown content with headings, bullet points, and code blocks but no speaker labels or timestamps, **When** it is analyzed, **Then** it is not classified as a transcript.

---

### Edge Cases

- What happens when an uploaded file is empty (0 bytes)? The system treats it as a non-transcript and falls through to normal processing. No error is shown to the user for the transcript detection step.
- What happens when a `.txt` file has exactly 2 speaker-label lines (below the threshold of 3)? The system does not classify it as a transcript, allowing it to pass through to normal processing. This avoids false positives from casual mentions of names with colons.
- What happens when a file contains mixed formats (e.g., speaker labels AND timestamps)? The system classifies it as a transcript if any single detection criterion is met, using the format with the highest confidence.
- What happens when the Transcribe agent fails to extract meaningful requirements from a valid transcript (e.g., the transcript is off-topic or too short)? The system returns whatever the agent produces; the user can review and decline the recommendation before any issue is created (Chat path only).
- What happens when multiple files are uploaded simultaneously in Chat, and some are transcripts while others are not? The system processes the first detected transcript file. Non-transcript files are handled through the normal flow.
- What happens when a `.vtt` or `.srt` file is malformed (e.g., missing headers, broken timestamp format)? The file is still classified as a transcript based on its extension, and the Transcribe agent processes it best-effort. The agent is designed to handle imperfect input.
- What happens when transcript content is extremely long (e.g., a 3-hour meeting)? The system processes the full transcript content. The Transcribe agent handles summarization and prioritization as part of its analysis.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept `.vtt` and `.srt` file uploads in the Chat interface alongside already-supported `.txt` and `.md` files.
- **FR-002**: System MUST accept `.vtt` and `.srt` file uploads in the Parent Issue Intake panel alongside already-supported file types.
- **FR-003**: System MUST detect whether an uploaded or pasted file/content is a meeting transcript using a combination of extension-based and content-based analysis.
- **FR-004**: System MUST always classify files with `.vtt` or `.srt` extensions as transcripts without content analysis.
- **FR-005**: System MUST analyze `.txt` and `.md` file content for transcript indicators: speaker labels (≥3 occurrences), timestamps (≥5 occurrences), or structural markers (e.g., "WEBVTT", "-->").
- **FR-006**: System MUST return a detection result that includes whether the content is a transcript, the detected format, and a confidence score.
- **FR-007**: System MUST route detected transcripts through a Transcribe agent that extracts user requirements, user stories, UI/UX preferences, and technical notes from multi-speaker conversations.
- **FR-008**: The Transcribe agent MUST output a structured recommendation containing: a title, user stories, UI/UX description, functional requirements, technical notes, and metadata.
- **FR-009**: The structured recommendation MUST be compatible with the existing issue recommendation workflow (review, confirm, create parent issue + sub-issues).
- **FR-010**: System MUST process transcripts in the Chat flow with higher priority than feature-request detection but lower priority than explicit agent commands.
- **FR-011**: System MUST process transcript content in the Parent Issue Intake flow before creating the GitHub issue, using the extracted requirements as the issue body.
- **FR-012**: System MUST NOT alter existing behavior for non-transcript files — they MUST continue to flow through normal processing (feature-request detection, etc.).
- **FR-013**: System MUST NOT require user confirmation before transcript analysis begins — detection and processing are fully automatic.
- **FR-014**: System MUST store a truncated excerpt (first 500 characters) of the original transcript as the input reference for the generated recommendation.

### Key Entities

- **TranscriptDetectionResult**: Represents the outcome of analyzing a file or content for transcript patterns. Key attributes: whether the content is a transcript (boolean), the detected format (vtt, srt, speaker_labeled, timestamped, or none), and a confidence score (0.0 to 1.0).
- **IssueRecommendation** *(existing, reused)*: Represents the structured output from the Transcribe agent. Contains a title, user story, UI/UX description, functional requirements, technical notes, and metadata. Already integrated into the issue creation workflow.

### Assumptions

- The existing `IssueRecommendation` model is sufficient to represent transcript analysis output without modifications.
- The existing issue recommendation preview UI and confirm-to-create workflow in Chat work as-is for transcript-generated recommendations.
- The existing `execute_full_workflow` and `create_all_sub_issues` pipeline flows handle transcript-generated issues without changes.
- Speaker labels in transcripts follow common patterns: "Name:", "[Name]:", "Speaker N:" — the detection does not need to support every possible format but should cover the most common ones.
- The Transcribe agent's AI prompt is designed for English-language transcripts. Multi-language support is not in scope.
- No new database migrations are required since `IssueRecommendation` already supports the needed fields including `file_urls`.
- Sub-issues are generated per pipeline agent, not per individual requirement extracted from the transcript.

### Out of Scope

- Audio or video transcription (ASR/speech-to-text) — only pre-existing text-based transcript files are supported.
- Real-time meeting capture or live transcription integration.
- Transcript editing UI — users cannot edit the transcript before analysis.
- Proprietary transcript formats (e.g., Otter.ai JSON, Zoom JSON exports, Microsoft Teams DOCX exports).
- Multi-language transcript analysis.
- User-configurable detection thresholds or format preferences.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can upload a `.vtt` or `.srt` transcript file in Chat and see a structured issue recommendation within 30 seconds.
- **SC-002**: Users can upload a transcript file in Parent Issue Intake and have a GitHub Parent Issue created with structured requirements in the body within 60 seconds of submission.
- **SC-003**: Transcript detection correctly identifies at least 95% of common transcript formats (VTT, SRT, speaker-labeled text, timestamped text) as transcripts.
- **SC-004**: Transcript detection produces zero false positives for standard prose documents, markdown documentation, and code files.
- **SC-005**: Non-transcript file uploads continue to work identically to their behavior before this feature — no regressions in existing Chat or Intake workflows.
- **SC-006**: The Transcribe agent extracts at least 3 distinct user stories or functional requirements from a transcript containing a 30-minute meeting with 2+ speakers.
- **SC-007**: 90% of users who upload a meeting transcript find the extracted requirements accurate enough to use as-is or with minor edits.
- **SC-008**: Both the Chat file picker and the Parent Issue Intake file picker accept `.vtt` and `.srt` files without requiring the user to change any settings or use workarounds.
