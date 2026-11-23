# Phrase Backend API Documentation

## Overview

**Base URL**: `/api`

**Authentication**: Most endpoints require authentication via Bearer token or cookie-based access token. Protected endpoints are clearly marked with their authentication requirements.

**Response Format**: All successful responses follow the `SuccessSchema` format:
```json
{
  "data": <response_data>,
  "message": "Request successful"
}
```

## Authentication

This API uses JWT (JSON Web Token) based authentication. There are two ways to authenticate:

### 1. Bearer Token (Authorization Header)
```
Authorization: Bearer <access_token>
```

### 2. Cookie (Browser clients)
- `access_token`: The JWT access token (automatically set by the server on login)
- `refresh_token`: The JWT refresh token (used for token refresh)

### Protected Endpoints
All endpoints marked with `[PROTECTED]` require a valid access token.

### Token Management
- **Access Token**: Valid for 24 hours, used for authenticating requests
- **Refresh Token**: Valid for 15 days, used to obtain new access tokens
- Both tokens are automatically set as cookies on login/logout endpoints

## Error Responses

| Status Code | Error Type | Description |
|-------------|------------|-------------|
| 400 | BadRequestException | Invalid request data, missing parameters, or validation errors |
| 401 | UnauthorizedException | Invalid or expired authentication token |
| 403 | ForbiddenException | User doesn't have required permissions |
| 404 | NotFoundException | Resource not found |
| 409 | ConflictException | Request conflicts with current state |
| 500 | InternalServerErrorException | Internal server error |
| 503 | UpstreamServiceDownException | Upstream service unavailable |

---

# Auth Module (`/auth`)

## Endpoints

### 1. Register User

**Endpoint**: `POST /auth/register`  
**Auth**: None  
**Description**: Register a new user account

#### Request Body

```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "name": "John Doe",
  "native_language": "en"
}
```

##### Request Fields

| Field | Type | Required | Description | Constraints |
|-------|------|----------|-------------|-------------|
| email | string | Yes | User email address | 3-30 characters |
| password | string | Yes | User password | 8-20 characters |
| name | string | No | User's display name | Max 20 characters |
| native_language | string | No | User's native language | Default: "en" (English) |

##### Enum Values: `native_language`

All 60+ supported language codes (see full enum reference at end).

#### Response

```json
{
  "data": {
    "user_id": 123
  },
  "message": "Account created successfully"
}
```

#### Possible Errors
- `400` - Email already registered
- `400` - Email or password validation error

---

### 2. Login User

**Endpoint**: `POST /auth/login`  
**Auth**: None  
**Description**: Authenticate user and receive access/refresh tokens

#### Request Body

```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

#### Response

```json
{
  "data": {
    "user_id": 123,
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  },
  "message": "User logged in successfully"
}
```

#### Possible Errors
- `400` - Invalid email or password

---

### 3. Logout

**Endpoint**: `POST /auth/logout`  
**Auth**: [PROTECTED] Requires access token  
**Description**: Log out user and invalidate refresh token

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| all_devices | boolean | false | Invalidate all user sessions |

#### Headers

| Header | Type | Required | Description |
|--------|------|----------|-------------|
| X-Refresh-Token | string | Conditional | Mobile clients |
| Cookie | - | Conditional | Browser clients |

#### Possible Errors
- `400` - Missing refresh token
- `401` - Invalid authentication token

---

### 4. Refresh Token

**Endpoint**: `POST /auth/refresh-token`  
**Auth**: None (but requires valid refresh token)

#### Headers

| Header | Type | Required | Description |
|--------|------|----------|-------------|
| X-Refresh-Token | string | Conditional | Mobile clients |
| Cookie | - | Conditional | Browser clients |

#### Response

```json
{
  "data": {
    "user_id": 123,
    "access_token": "...",
    "refresh_token": "..."
  },
  "message": "Token refreshed successfully"
}
```

#### Possible Errors
- `400` - Missing refresh token or invalid scheme
- `401` - Invalid or expired refresh token

---

### 5. Generate OTP

**Endpoint**: `POST /auth/otp`  
**Auth**: [PROTECTED] Requires access token  
**Description**: Generate a 6-digit OTP for email verification (cached in Redis for 10 minutes)

#### Request Body

```json
{
  "email": "user@example.com"
}
```

#### Response

```json
{
  "data": 123456
}
```

#### Possible Errors
- `400` - User is already verified
- `404` - User not found

---

### 6. Verify OTP

**Endpoint**: `POST /auth/otp-validate`  
**Auth**: [PROTECTED] Requires access token  
**Description**: Verify OTP and mark user as verified

#### Request Body

```json
{
  "email": "user@example.com",
  "otp": 123456
}
```

#### Possible Errors
- `400` - OTP is expired or invalid
- `404` - User not found
- `400` - User is already verified

---

### 7. Request Password Reset

**Endpoint**: `POST /auth/request-reset-password`  
**Auth**: None  
**Description**: Request OTP for password reset

#### Request Body

```json
{
  "email": "user@example.com"
}
```

#### Possible Errors
- `404` - User not found

---

### 8. Verify Password Reset

**Endpoint**: `POST /auth/verify-reset-password`  
**Auth**: None  
**Description**: Verify OTP and set new password

#### Request Body

```json
{
  "email": "user@example.com",
  "otp": 123456,
  "password": "newpassword123"
}
```

#### Possible Errors
- `400` - OTP is expired or invalid
- `404` - User not found

---

# User Module (`/users`)

## Endpoints

### 1. Get Current User

**Endpoint**: `GET /users/me`  
**Auth**: [PROTECTED] Requires access token  
**Description**: Get the authenticated user's profile information

#### Response

```json
{
  "data": {
    "id": 123,
    "email": "user@example.com",
    "name": "John Doe",
    "provider": "local",
    "is_verified": true,
    "account_status": "active",
    "role": "user",
    "native_language": "en",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  },
  "message": "Request successful"
}
```

##### Enum Values

| Enum | Values | Description |
|------|--------|-------------|
| provider | `local`, `google`, `apple` | Authentication method |
| account_status | `active`, `inactive`, `suspended`, `banned` | Account state |
| role | `admin`, `user`, `guest` | User permissions level |

#### Possible Errors
- `401` - Invalid or expired authentication token

---

### 2. Get User Subscriptions

**Endpoint**: `GET /users/subscription`  
**Auth**: [PROTECTED] Requires access token  
**Description**: Get all subscriptions for the authenticated user

#### Response

```json
{
  "data": [
    {
      "id": 1,
      "user_id": 123,
      "plan_id": 1,
      "provider": "dodo_payments",
      "provider_sub_id": "sub_xxx",
      "status": "active",
      "quantity": 1,
      "current_period_start": "2024-01-01T00:00:00Z",
      "current_period_end": "2024-02-01T00:00:00Z",
      "cancel_at_period_end": false,
      "canceled_at": null,
      "version": 1,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ],
  "message": "Request successful"
}
```

##### Enum Values: `status`

| Value | Description |
|-------|-------------|
| `active` | Subscription is active |
| `canceled` | Subscription has been canceled |
| `past_due` | Payment is overdue |
| `unpaid` | Payment failed |
| `trialing` | Currently in trial period |

#### Possible Errors
- `401` - Invalid or expired authentication token

---

### 3. Get User by ID (Admin Only)

**Endpoint**: `GET /users/{user_id}`  
**Auth**: [PROTECTED] Requires `admin` role  
**Description**: Get detailed user information

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| user_id | integer | Yes | The user's ID |

#### Possible Errors
- `401` - Invalid or expired authentication token
- `403` - User is not an admin

---

# Title Module (`/title`)

## Endpoints

### 1. Discover Content

**Endpoint**: `GET /title/discover`  
**Auth**: None  
**Description**: Discover movies or TV shows (cached for 3 days)

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| discover_type | string | `popular` | Discovery type |
| feature_type | string | `movie` | Content type |
| language_code | string | `all` | Filter by language |

##### Enum Values

| Parameter | Values | Description |
|-----------|--------|-------------|
| discover_type | `popular`, `latest` | How content is sorted |
| feature_type | `movie`, `tvshow` | Type of content |

#### Response

```json
{
  "data": [
    {
      "id": "123456",
      "type": "movie",
      "attributes": {
        "title": "Movie Title",
        "original_title": "Movie Title",
        "year": 2024,
        "subtitles_count": 0,
        "seasons_count": 0,
        "subtitles_counts": {},
        "parent_title": null,
        "season_number": null,
        "episode_number": null,
        "imdb_id": 123456,
        "tmdb_id": null,
        "parent_imdb_id": null,
        "feature_id": "123456",
        "title_aka": [],
        "img_url": "https://...",
        "seasons": []
      }
    }
  ],
  "message": "Request successful"
}
```

**Notes:**
- Response uses `SearchResponseSchema` format
- Cached for 3 days in Redis

#### Edge Cases

**When `feature_type` changes:**
- `feature_type=movie`: Returns movies only, `seasons` is empty array `[]`
- `feature_type=tvshow`: Returns TV shows only, `seasons` contains season data

**When `language_code` changes:**
- `language_code=all`: All languages
- `language_code=en`: English content only

#### Possible Errors
- `503` - OpenSubtitles API unavailable

---

### 2. Search Content

**Endpoint**: `GET /title/search`  
**Auth**: None  
**Description**: Search for movies or TV shows (cached for 3 days)

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| feature_id | integer | - | Feature ID from OpenSubtitles |
| full_search | boolean | false | Full text search |
| imdb_id | string | - | IMDb ID |
| tmdb_id | string | - | TheMovieDB ID |
| query | string | - | Search query text |
| query_match | string | `start` | How to match query |
| type | string | - | Content type filter |
| year | integer | - | Release year |

##### Enum Values: `query_match`

| Value | Description |
|-------|-------------|
| `start` | Match at start of title |
| `word` | Match whole words |
| `exact` | Exact match only |

##### Enum Values: `type`

| Value | Description |
|-------|-------------|
| `movie` | Movie content |
| `tvshow` | TV show content |
| `episode` | Episode content |

#### Request Example

```
GET /title/search?query=matrix&year=1999&type=movie
```

#### Possible Errors
- `400` - No search parameters provided
- `503` - OpenSubtitles API unavailable

**Notes:**
- At least one search parameter required: `feature_id`, `imdb_id`, `tmdb_id`, or `query`

#### Edge Cases

**When `type` is `tvshow`:**
- Response includes `seasons` array with season data
- `seasons_count` indicates number of seasons
- `seasons` contains season objects with episodes

**When `type` is `movie`:**
- `seasons` is empty array `[]`
- `seasons_count` is 0

**When `type` is `episode`:**
- `parent_imdb_id` contains parent show's IMDb
- `season_number` and `episode_number` are populated

---

### 3. Get Title Translations (UPDATED)

**Endpoint**: `GET /title/{imdb_id}`  
**Auth**: None  
**Description**: Get translations for a specific title

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| imdb_id | string | Yes | IMDb ID (e.g., "tt1234567") |

#### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| language_code | string | Yes | - | Target language code |

#### Response

```json
{
  "data": [
    {
      "id": 1,
      "content_uid": "550e8400-e29b-41d4-a716-446655440000",
      "language_code": "en",
      "difficulty_level": "easy",
      "category": "word",
      "original_sentence_or_word": "Hello",
      "source_sentence": "Hello, how are you?",
      "canonical_form": "hello",
      "explanation": ["A common greeting"],
      "speech_register": ["neutral", "formal"],
      "tone": ["friendly"],
      "confidence": "high",
      "context_note": null,
      "usage": [
        {
          "type": "Example",
          "explanation": "Hello, how are you doing?"
        }
      ]
    }
  ],
  "message": "Request successful"
}
```

##### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| id | integer | Translation ID |
| content_uid | UUID | Content unique identifier |
| language_code | string | Language code |
| difficulty_level | string | Difficulty level (enum) |
| category | string | Category (enum) |
| original_sentence_or_word | string | Extracted text from subtitle |
| source_sentence | string | Complete original sentence |
| canonical_form | string | Reusable dictionary form |
| explanation | array of strings | Explanations in native language |
| speech_register | array of strings | Speech register types |
| tone | array of strings | Emotional/conversational tone |
| confidence | string | Reliability (enum) |
| context_note | string \| null | Ambiguity notes |
| usage | array of Usage objects | Usage examples |

##### Enum Values: `difficulty_level`

| Value | Description |
|-------|-------------|
| `easy` | Easy to understand |
| `medium` | Medium difficulty |
| `hard` | Advanced level |

##### Enum Values: `category`

**Vocabulary:** `word`, `phrasal_verb`, `idiom`, `expression`, `slang`, `collocation`, `proverb`

**Sentence Structures:** `sentence_pattern`, `conversational_phrase`, `complete_sentence`

**Grammar:** `grammar_rule`, `tense`, `modal_verb`, `conditional`, `voice`, `clause`, `preposition`, `conjunction`, `other_grammar`

##### Enum Values: `speech_register`

| Value | Description |
|-------|-------------|
| `formal` | Formal register |
| `neutral` | Neutral register |
| `informal` | Informal register |
| `slang` | Slang |
| `vulgar` | Vulgar |
| `literary` | Literary |
| `regional` | Regional |

##### Enum Values: `tone`

| Value | Description |
|-------|-------------|
| `sarcastic`, `humorous`, `polite`, `rude`, `affectionate` |
| `annoyed`, `angry`, `friendly`, `persuasive`, `dismissive` |
| `serious`, `playful`, `other` |

##### Enum Values: `confidence`

| Value | Description |
|-------|-------------|
| `high` | High confidence |
| `medium` | Medium confidence |
| `low` | Low confidence |

##### Enum Values: `usage.type`

| Value | Description |
|-------|-------------|
| `Example` | Example usage |
| `Grammar` | Grammar explanation |
| `Context` | Context explanation |
| `Common Expression` | Common expression |
| `Alternative Expression` | Alternative expression |
| `Pronunciation` | Pronunciation info |
| `Common Mistake` | Common mistake |

##### Usage Object

```json
{
  "type": "Example",
  "explanation": "Hello, how are you doing?"
}
```

#### Edge Cases

**When `language_code` changes:**
- `language_code="en"`: English phrases with Hindi explanations
- `language_code="hi"`: Hindi phrases with English explanations
- `language_code="es"`: Spanish phrases with English explanations

**When title doesn't exist:**
- Title is fetched from OpenSubtitles API
- Subtitles are processed through LLM
- New translations are created and cached

**When title exists in database:**
- Translations are retrieved from database cache
- No additional API calls or processing
- Faster response time

#### Possible Errors
- `404` - Subtitle file not found
- `404` - Title not found
- `500` - Internal server error

---

# Chat Module (`/chat`)

## Endpoints

### 1. List User Chats

**Endpoint**: `GET /chat`  
**Auth**: [PROTECTED] Requires access token  
**Description**: List user's chat sessions with pagination

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| after_uid | UUID | - | Last chat UID for pagination |
| after_date | float | - | Unix timestamp for pagination |
| limit | integer | 20 | Number of chats per page (1-50) |

#### Response

```json
{
  "data": {
    "items": [
      {
        "uid": "550e8400-e29b-41d4-a716-446655440000",
        "title": "First Chat",
        "updated_at": "2024-01-01T00:00:00Z",
        "created_at": "2024-01-01T00:00:00Z"
      }
    ],
    "has_more": false,
    "after_uid": "550e8400-e29b-41d4-a716-446655440000",
    "after_date": 1704067200.0
  },
  "message": "Request successful"
}
```

#### Edge Cases

**When `limit` is 1:** Returns single chat, pagination cursor still populated

**When `limit` is 50:** Returns maximum 50 chats per request

**When `after_uid` and `after_date` are provided:** Returns chats after that cursor (keyset pagination)

#### Possible Errors
- `400` - Invalid parameter values
- `401` - Invalid or expired authentication token

---

### 2. Create New Chat Session

**Endpoint**: `POST /chat`  
**Auth**: [PROTECTED] Requires access token  
**Description**: Create a new chat session

#### Request Body

```json
{
  "message_uid": "550e8400-e29b-41d4-a716-446655440000",
  "content": "This is my first message"
}
```

#### Response

**HTTP 303 See Other** redirect to: `/api/chat/{uid}/message`

#### Possible Errors
- `400` - Message content is empty

---

### 3. Delete Chat Session

**Endpoint**: `DELETE /chat/{uid}`  
**Auth**: [PROTECTED] Requires access token  
**Description**: Delete a chat session and all its messages

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| uid | UUID | Yes | Chat session ID to delete |

#### Possible Errors
- `400` - Chat not found
- `401` - Invalid or expired authentication token

---

### 4. Get Chat Messages

**Endpoint**: `GET /chat/{uid}/message`  
**Auth**: [PROTECTED] Requires access token  
**Description**: Get messages for a specific chat session

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| uid | UUID | Yes | Chat session ID |

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| after_uid | integer | - | Last message ID for pagination |
| after_date | float | - | Unix timestamp for pagination |
| limit | integer | 10 | Number of messages per page (1-50) |

#### Possible Errors
- `401` - Invalid or expired authentication token

---

### 5. Chat with AI (Streaming)

**Endpoint**: `POST /chat/{uid}/message`  
**Auth**: [PROTECTED] Requires access token  
**Description**: Send message to AI chat and receive streaming response

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| uid | UUID | Yes | Chat session ID |

#### Request Body

```json
{
  "message_uid": "550e8400-e29b-41d4-a716-446655440000",
  "content": "What does 'hello' mean in Spanish?"
}
```

#### Response

**Content-Type**: `text/event-stream`

```
data: {"message_uid":"...","content":"Hola","status":"loading"}
data: {"message_uid":"...","content":"","status":"success"}
```

##### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| message_uid | UUID | Client-provided message ID |
| content | string \| null | Streamed content chunk |
| status | string | Message status (enum) |

##### Enum Values: `status`

| Value | Description |
|-------|-------------|
| `loading` | Content being generated |
| `cached` | Response from cache |
| `success` | Complete |
| `error` | Error occurred |

#### Idempotency

The endpoint supports idempotency via `message_uid`. If the same `message_uid` is sent within 12 hours, the cached response is returned.

#### Edge Cases

**When `message_uid` is duplicate (within 12 hours):**
- Returns cached response with `status: "cached"`
- No new message processed by AI

**When `message_uid` is new:**
- User message is stored in database
- AI processes and streams response
- Response is cached for 12 hours

**When plan has insufficient quota:**
- Stream returns error message
- HTTP 400 error

#### Background Tasks

After message processing:
- User message embedding is stored
- Feature usage is tracked
- LLM usage metrics are recorded

#### Possible Errors

**Stream Errors:**
```
data: {"message_uid":"...","content":"Sorry, I encountered an error processing your request.","status":"error"}
```

**Authentication Errors:**
- `401` - Invalid or expired authentication token

**Business Logic Errors:**
- `400` - Plan has insufficient feature quota

---

# Feature Module (`/feature`)

## Endpoints

### 1. List Features (Admin Only)

**Endpoint**: `GET /feature/feature`  
**Auth**: [PROTECTED] Requires `admin` role  
**Description**: List all registered features

#### Response

```json
{
  "data": [
    {
      "id": 1,
      "name": "Chat",
      "description": "AI chat features",
      "quantity": 1000,
      "unit": "request",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "message": "Request successful"
}
```

##### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| id | integer | Feature ID |
| name | string | Feature name |
| description | string | Feature description |
| quantity | integer | Feature quantity (stored as string, returned as integer) |
| unit | string | Usage unit (enum) |
| created_at | datetime | Creation timestamp |

##### Enum Values: `unit`

| Value | Description |
|-------|-------------|
| `request` | Number of requests |
| `tokens` | Number of tokens |
| `characters` | Number of characters |

**CORRECTION**: The `unit` field accepts: `request`, `tokens`, or `characters`

#### Possible Errors
- `401` - Invalid or expired authentication token
- `403` - User is not an admin

---

### 2. Register Feature (Admin Only)

**Endpoint**: `POST /feature/feature`  
**Auth**: [PROTECTED] Requires `admin` role  
**Description**: Register a new feature

#### Request Body

```json
{
  "name": "Translation",
  "description": "Subtitle translation service",
  "quantity": 500,
  "unit": "request"
}
```

##### Request Fields

| Field | Type | Required | Description | Constraints |
|-------|------|----------|-------------|-------------|
| name | string | Yes | Feature name | Max 100 characters |
| description | string | Yes | Feature description | Max 255 characters |
| quantity | integer | Yes | Feature quantity | Positive integer |
| unit | string | Yes | Usage unit | `request`, `tokens`, or `characters` |

**CORRECTION**: The `unit` field accepts: `request`, `tokens`, or `characters`

#### Response

```json
{
  "data": {
    "id": 1,
    "name": "Translation",
    "description": "Subtitle translation service",
    "quantity": 500,
    "unit": "request",
    "created_at": "2024-01-01T00:00:00Z"
  },
  "message": "Request successful"
}
```

#### Possible Errors
- `400` - Validation error
- `401` - Invalid or expired authentication token
- `403` - User is not an admin

---

### 3. List Plans

**Endpoint**: `GET /feature/plan`  
**Auth**: [PROTECTED] Requires `admin` role  
**Description**: List all plans with their features

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| status | string | `active` | Plan status filter |

##### Enum Values: `status`

| Value | Description |
|-------|-------------|
| `active` | Active plans |
| `discountinued` | Discontinued plans |

#### Possible Errors
- `401` - Invalid or expired authentication token
- `403` - User is not an admin

---

### 4. Create New Plan (Admin Only)

**Endpoint**: `POST /feature/plan`  
**Auth**: [PROTECTED] Requires `admin` role  
**Description**: Create a new subscription plan

#### Request Body

```json
{
  "name": "Pro Plan",
  "price_amount": 999.00,
  "benefit": "All features included",
  "status": "active",
  "plan_billing_type": "monthly"
}
```

##### Enum Values: `plan_billing_type`

| Value | Description |
|-------|-------------|
| `monthly` | Monthly billing |
| `yearly` | Yearly billing |

#### Possible Errors
- `400` - Validation error
- `401` - Invalid or expired authentication token
- `403` - User is not an admin

---

### 5. Edit Plan (Admin Only)

**Endpoint**: `PATCH /feature/plan`  
**Auth**: [PROTECTED] Requires `admin` role  
**Description**: Update an existing plan

#### Request Body

```json
{
  "id": 1,
  "price_amount": 1299.00,
  "benefit": "Updated benefits",
  "status": "active"
}
```

**Note**: At least one field must be provided.

#### Possible Errors
- `400` - Validation error (no fields provided)
- `401` - Invalid or expired authentication token
- `403` - User is not an admin

---

### 6. Delete Plan (Admin Only)

**Endpoint**: `DELETE /feature/plan/{plan_id}`  
**Auth**: [PROTECTED] Requires `admin` role  
**Description**: Delete a plan (only if not used by subscriptions)

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| plan_id | integer | Yes | Plan ID to delete |

**Note**: Plan can only be deleted if no subscriptions reference it.

#### Possible Errors
- `401` - Invalid or expired authentication token
- `403` - User is not an admin
- `404` - Plan not found

---

### 7. List Plan Features

**Endpoint**: `GET /feature/plan/feature`  
**Auth**: [PROTECTED] Requires `admin` role  
**Description**: List all plans with their associated features

#### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| plan_status | string | No | - | Filter by plan status |
| billing_type | string | No | - | Filter by billing type |

##### Enum Values

| Parameter | Values | Description |
|-----------|--------|-------------|
| plan_status | `active`, `discountinued` | Plan status filter |
| billing_type | `monthly`, `yearly` | Billing type filter |

#### Response

```json
{
  "data": [
    {
      "plan_id": 1,
      "author_id": 1,
      "name": "Free",
      "price_amount": 0.0,
      "benefit": "Basic features",
      "status": "active",
      "plan_billing_type": "monthly",
      "created_at": "2024-01-01T00:00:00Z",
      "update_at": "2024-01-01T00:00:00Z",
      "features": [
        {
          "plan_feature_id": 1,
          "id": 1,
          "name": "Chat",
          "description": "AI chat features",
          "quantity": 1000,
          "unit": "request",
          "created_at": "2024-01-01T00:00:00Z"
        }
      ]
    }
  ],
  "message": "Request successful"
}
```

**Notes:**
- Returns grouped data with features per plan
- Supports optional status and billing type filters

#### Possible Errors
- `401` - Invalid or expired authentication token
- `403` - User is not an admin

---

### 8. Register Plan Feature (Admin Only)

**Endpoint**: `POST /feature/plan/feature`  
**Auth**: [PROTECTED] Requires `admin` role  
**Description**: Add a feature to a plan

#### Request Body

```json
{
  "plan_id": 1,
  "feature_id": 2,
  "usage_limit": 1000
}
```

#### Response

```json
{
  "data": {
    "id": 1,
    "plan_id": 1,
    "feature_id": 2,
    "usage_limit": 1000,
    "created_at": "2024-01-01T00:00:00Z"
  },
  "message": "Request successful"
}
```

#### Possible Errors
- `401` - Invalid or expired authentication token
- `403` - User is not an admin

---

### 9. Delete Plan Feature (Admin Only)

**Endpoint**: `DELETE /feature/plan/feature/{plan_feature_id}`  
**Auth**: [PROTECTED] Requires `admin` role  
**Description**: Remove a feature from a plan

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| plan_feature_id | integer | Yes | Plan-feature mapping ID |

#### Possible Errors
- `401` - Invalid or expired authentication token
- `403` - User is not an admin
- `404` - Plan feature not found

---

# Billing Module (`/billing`)

## Endpoints

### 1. Get Pricing Information

**Endpoint**: `GET /billing/pricing`  
**Auth**: None  
**Description**: Get pricing information for all active plans

#### Response

```json
[
  {
    "plan_id": 1,
    "author_id": 1,
    "name": "Free",
    "price_amount": 0.0,
    "benefit": "Basic features",
    "status": "active",
    "plan_billing_type": "monthly",
    "created_at": "2024-01-01T00:00:00Z",
    "update_at": "2024-01-01T00:00:00Z",
    "features": [
      {
        "id": 1,
        "name": "Chat",
        "description": "AI chat features",
        "quantity": 1000,
        "unit": "request",
        "created_at": "2024-01-01T00:00:00Z"
      }
    ]
  }
]
```

**Notes:**
- Returns only active plans
- Grouped with features for each plan
- No authentication required

---

### 2. Checkout / Create Subscription

**Endpoint**: `POST /billing/checkout`  
**Auth**: [PROTECTED] Requires access token  
**Description**: Create a new subscription via payment provider

#### Request Body

```json
{
  "plan_id": 1
}
```

#### Possible Errors
- `400` - Invalid plan ID
- `400` - User already has active subscription
- `401` - Invalid or expired authentication token

---

# Webhooks Module (Root Level)

## Endpoints

### 1. Payment Webhook

**Endpoint**: `POST /webhooks/payment`  
**Auth**: None (but should validate signature)  
**Description**: Handle payment provider webhooks

**Notes:**
- Currently logs raw body for debugging
- Should implement signature verification in production
- Used for handling subscription events from payment provider

---

# Enum Reference

## All Available Enums

### AccountStatus
- `active`, `inactive`, `suspended`, `banned`

### UserRole
- `admin`, `user`, `guest`

### ProviderType
- `local`, `google`, `apple`

### FeatureType
- `movie`, `tvshow`

### Language (Full List - 60+ languages)
`en`, `hi`, `es`, `fr`, `de`, `it`, `pt`, `ru`, `zh`, `ja`, `ko`, `ar`, `fa`, `sv`, `nl`, `pl`, `cs`, `hu`, `ro`, `bg`, `hr`, `sk`, `sl`, `et`, `lv`, `lt`, `fi`, `da`, `no`, `is`, `cy`, `gd`, `gl`, `eu`, `ca`, `va`, `fy`, `br`, `kw`, `sco`, `gv`, `el`, `he`, `yi`, `th`, `vi`, `id`, `tl`, `ms`, `fil`, `ht`, `sr`, `bs`, `mk`, `sq`, `hy`, `ka`, `az`, `uz`, `kk`, `ky`, `tk`, `uk`, `zh-TW`, `zh-CN`, `pt-BR`, `pt-PT`, `ta`, `te`, `ml`, `kn`, `mr`, `gu`, `pa`, `bn`, `or`, `as`, `mizo`, `ks`, `ne`, `sd`, `ur`, `brx`, `mni`, `sa`, `other`

### FeatureUnit (Updated)
- `request` - Number of requests
- `tokens` - Number of tokens
- `characters` - Number of characters

### SubscriptionStatus
- `active`, `canceled`, `past_due`, `unpaid`, `trialing`

### PlansStatus
- `active`, `discountinued`

### PlansBillingType
- `monthly`, `yearly`

### EventType
- `created`, `updated`, `status_changed`, `trial_started`, `trial_ended`
- `plan_changed`, `qty_changed`, `payment_failed`, `payment_recovered`
- `canceled`, `renewed`

### Reason
- `payment_failed`, `user_request`, `admin_action`, `dunning`, `fraud`

### ActorType
- `user`, `admin`, `system`, `provider`

### DiscoverType
- `popular`, `latest`

### ChatRoleType
- `user`, `assistant`

### ChatMessageStatus
- `pending`, `failed`, `success`

### QueryMatchType
- `start`, `word`, `exact`

### TitleType
- `movie`, `episode`, `tvshow`

---

# Request/Response Examples

## Complete Auth Flow

### 1. Register
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"securepassword123","name":"John Doe","native_language":"en"}'
```

### 2. Login
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"securepassword123"}'
```

### 3. Access Protected Endpoint
```bash
curl -X GET http://localhost:8000/api/users/me \
  -H "Authorization: Bearer <access_token>"
```

### 4. Refresh Token
```bash
curl -X POST http://localhost:8000/api/auth/refresh-token \
  -H "Authorization: Bearer <refresh_token>"
```

## Chat Flow Example

### 1. Create Chat
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"message_uid":"550e8400-e29b-41d4-a716-446655440000","content":"Hello"}'
```

### 2. Send Message (Streaming)
```bash
curl -X POST http://localhost:8000/api/chat/{chat_uid}/message \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"message_uid":"550e8400-e29b-41d4-a716-446655440001","content":"What does this phrase mean?"}'
```

---

# Best Practices

## Authentication
1. Store access tokens securely (memory for web, secure storage for mobile)
2. Implement automatic token refresh before expiration
3. Use cookies for browser clients for automatic token handling
4. Implement token revocation on logout

## Pagination
1. Use `after_uid` and `after_date` for keyset pagination
2. Store pagination cursor for resume capability
3. Handle `has_more` flag to show "Load more" buttons

## Error Handling
1. Check for 401 errors and redirect to login
2. Implement retry logic with exponential backoff for 5xx errors
3. Show user-friendly error messages
4. Log detailed errors for debugging

## Rate Limiting
1. Implement request throttling on the client side
2. Cache responses where applicable
3. Use streaming for long-running operations
