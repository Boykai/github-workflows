# Data Model: Chat Document Upload

**Feature Branch**: `001-chat-document-upload`  
**Created**: 2026-02-13

## Entity Relationships

```
ChatMessage (extended)
  ├── action_data.document (new)
  └── conversation_id (existing)

ChatConversation (existing)
  └── participants (for access control)
```

## Entity: ChatMessage (Extended)

**Purpose**: Existing entity extended to support document attachments

**Extension**: Add document metadata to `action_data` field

### Schema Extension

```python
class ChatMessage:
    # Existing fields...
    id: str
    conversation_id: str
    sender_id: str
    content: str
    timestamp: datetime
    action_data: dict  # Extended to support document attachments
```

### action_data Schema for Document Upload

```python
{
    "type": "document_upload",
    "document": {
        "filename": str,              # Original filename
        "file_size": int,             # Size in bytes
        "file_type": str,             # MIME type (application/pdf, etc.)
        "storage_path": str,          # Relative path in storage
        "upload_timestamp": str,      # ISO 8601 timestamp
        "document_id": str            # Unique identifier for download
    }
}
```

### Example

```python
{
    "id": "msg_123",
    "conversation_id": "conv_456",
    "sender_id": "user_789",
    "content": "Here's the quarterly report",
    "timestamp": "2026-02-13T21:50:00Z",
    "action_data": {
        "type": "document_upload",
        "document": {
            "filename": "Q4_Report.pdf",
            "file_size": 2457600,  # ~2.4 MB
            "file_type": "application/pdf",
            "storage_path": "uploads/conv_456/msg_123_Q4_Report.pdf",
            "upload_timestamp": "2026-02-13T21:50:00Z",
            "document_id": "doc_123"
        }
    }
}
```

## Entity: DocumentAttachment (Virtual)

**Purpose**: Represents document metadata (not a separate table, embedded in ChatMessage)

**Fields**:
- `filename`: Original filename (string, max 255 chars)
- `file_size`: Size in bytes (integer, max 20MB = 20971520 bytes)
- `file_type`: MIME type (string, enum: application/pdf, application/vnd.openxmlformats-officedocument.wordprocessingml.document, text/plain)
- `storage_path`: Relative file path (string)
- `upload_timestamp`: Upload time (ISO 8601 string)
- `document_id`: Unique identifier (string)

## Entity: ChatConversation (Existing)

**Purpose**: Existing entity used for access control

**Relevant Fields**:
- `id`: Conversation identifier
- `participants`: List of user IDs with access to the conversation

**Usage**: Verify document access by checking if user is participant

## Storage Structure

### Filesystem Layout

```
uploads/
  conv_456/                    # Conversation ID
    msg_123_Q4_Report.pdf      # Message ID + filename
    msg_124_budget.docx
    msg_125_notes.txt
```

### Naming Convention

Pattern: `{message_id}_{sanitized_filename}`

**Benefits**:
- Unique per message (no conflicts)
- Traceable to message
- Human-readable

## Validation Rules

### File Size
- Maximum: 20MB (20,971,520 bytes)
- Validation: Client and server

### File Type
- Allowed MIME types:
  - `application/pdf`
  - `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
  - `text/plain`
- Validation: Server-side using python-magic

### Filename
- Sanitization: Remove special characters, limit length
- Max length: 255 characters
- Pattern: Alphanumeric, hyphens, underscores, dots

## Access Control

**Rule**: User can access document if and only if they are a participant in the conversation

**Implementation**:
1. Extract conversation_id from message
2. Verify user_id in conversation.participants
3. Serve file if authorized, 403 otherwise

## Migration Notes

**Existing Data**: No schema migration needed - ChatMessage.action_data already exists as flexible JSON field

**Backward Compatibility**: Messages without documents continue to work (action_data is optional)
