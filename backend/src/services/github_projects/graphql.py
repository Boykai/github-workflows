"""GraphQL queries, mutations, and fragments for GitHub Projects V2 API."""

GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"

# T057: Rate limit configuration
MAX_RETRIES = 3
INITIAL_BACKOFF_SECONDS = 1
MAX_BACKOFF_SECONDS = 30


# GraphQL fragments for reusable field selections
PROJECT_FIELDS_FRAGMENT = """
fragment ProjectFields on ProjectV2 {
  id
  title
  url
  shortDescription
  closed
  field(name: "Status") {
    ... on ProjectV2SingleSelectField {
      id
      options {
        id
        name
        color
      }
    }
  }
  items(first: 1) {
    totalCount
  }
}
"""

# GraphQL queries
LIST_USER_PROJECTS_QUERY = (
    PROJECT_FIELDS_FRAGMENT
    + """
query($login: String!, $first: Int!) {
  user(login: $login) {
    projectsV2(first: $first) {
      nodes {
        ...ProjectFields
      }
    }
  }
}
"""
)

LIST_ORG_PROJECTS_QUERY = (
    PROJECT_FIELDS_FRAGMENT
    + """
query($login: String!, $first: Int!) {
  organization(login: $login) {
    projectsV2(first: $first) {
      nodes {
        ...ProjectFields
      }
    }
  }
}
"""
)

GET_PROJECT_ITEMS_QUERY = """
query($projectId: ID!, $first: Int!, $after: String) {
  node(id: $projectId) {
    ... on ProjectV2 {
      items(first: $first, after: $after) {
        pageInfo {
          hasNextPage
          endCursor
        }
        nodes {
          id
          fieldValueByName(name: "Status") {
            ... on ProjectV2ItemFieldSingleSelectValue {
              name
              optionId
            }
          }
          content {
            ... on DraftIssue {
              title
              body
            }
            ... on Issue {
              id
              number
              title
              body
              repository {
                owner {
                  login
                }
                name
              }
            }
            ... on PullRequest {
              id
              number
              title
              body
              repository {
                owner {
                  login
                }
                name
              }
            }
          }
        }
      }
    }
  }
}
"""

CREATE_DRAFT_ITEM_MUTATION = """
mutation($projectId: ID!, $title: String!, $body: String) {
  addProjectV2DraftIssue(input: {projectId: $projectId, title: $title, body: $body}) {
    projectItem {
      id
    }
  }
}
"""

UPDATE_ITEM_STATUS_MUTATION = """
mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $optionId: String!) {
  updateProjectV2ItemFieldValue(
    input: {
      projectId: $projectId
      itemId: $itemId
      fieldId: $fieldId
      value: { singleSelectOptionId: $optionId }
    }
  ) {
    projectV2Item {
      id
    }
  }
}
"""

# T019: GraphQL mutation to add existing issue to project
ADD_ISSUE_TO_PROJECT_MUTATION = """
mutation($projectId: ID!, $contentId: ID!) {
  addProjectV2ItemById(input: {projectId: $projectId, contentId: $contentId}) {
    item {
      id
    }
  }
}
"""

# Query to get project field info for status updates
GET_PROJECT_FIELD_QUERY = """
query($projectId: ID!) {
  node(id: $projectId) {
    ... on ProjectV2 {
      field(name: "Status") {
        ... on ProjectV2SingleSelectField {
          id
          options {
            id
            name
          }
        }
      }
    }
  }
}
"""

# Query to get repository info from project items (for issue creation target)
GET_PROJECT_REPOSITORY_QUERY = """
query($projectId: ID!) {
  node(id: $projectId) {
    ... on ProjectV2 {
      items(first: 10) {
        nodes {
          content {
            ... on Issue {
              repository {
                owner {
                  login
                }
                name
              }
            }
            ... on PullRequest {
              repository {
                owner {
                  login
                }
                name
              }
            }
          }
        }
      }
    }
  }
}
"""

# GraphQL mutation to assign Copilot to an issue with agent assignment config
# Requires headers: GraphQL-Features: issues_copilot_assignment_api_support,coding_agent_model_selection
ASSIGN_COPILOT_MUTATION = """
mutation($issueId: ID!, $assigneeIds: [ID!]!, $repoId: ID!, $baseRef: String!, $customInstructions: String!, $customAgent: String!) {
  addAssigneesToAssignable(input: {
    assignableId: $issueId,
    assigneeIds: $assigneeIds,
    agentAssignment: {
      targetRepositoryId: $repoId,
      baseRef: $baseRef,
      customInstructions: $customInstructions,
      customAgent: $customAgent,
      model: "claude-opus-4.6"
    }
  }) {
    assignable {
      ... on Issue {
        id
        assignees(first: 10) {
          nodes {
            login
          }
        }
      }
    }
  }
}
"""

# GraphQL query to get issue details including title, body, and comments
GET_ISSUE_WITH_COMMENTS_QUERY = """
query($owner: String!, $name: String!, $number: Int!) {
  repository(owner: $owner, name: $name) {
    issue(number: $number) {
      id
      title
      body
      comments(first: 100) {
        nodes {
          id
          author {
            login
          }
          body
          createdAt
        }
      }
    }
  }
}
"""

# GraphQL query to get suggested actors (including Copilot bot) for a repository
GET_SUGGESTED_ACTORS_QUERY = """
query($owner: String!, $name: String!) {
  repository(owner: $owner, name: $name) {
    id
    suggestedActors(capabilities: [CAN_BE_ASSIGNED], first: 100) {
      nodes {
        login
        __typename
        ... on Bot {
          id
        }
        ... on User {
          id
        }
      }
    }
  }
}
"""

# GraphQL query to get linked pull requests for an issue
GET_ISSUE_LINKED_PRS_QUERY = """
query($owner: String!, $name: String!, $number: Int!) {
  repository(owner: $owner, name: $name) {
    issue(number: $number) {
      id
      title
      state
      timelineItems(itemTypes: [CONNECTED_EVENT, CROSS_REFERENCED_EVENT], first: 50) {
        nodes {
          ... on ConnectedEvent {
            subject {
              ... on PullRequest {
                id
                number
                title
                state
                isDraft
                url
                headRefName
                author {
                  login
                }
                createdAt
                updatedAt
              }
            }
          }
          ... on CrossReferencedEvent {
            source {
              ... on PullRequest {
                id
                number
                title
                state
                isDraft
                url
                headRefName
                author {
                  login
                }
                createdAt
                updatedAt
              }
            }
          }
        }
      }
    }
  }
}
"""

# GraphQL mutation to mark a draft PR as ready for review
MARK_PR_READY_FOR_REVIEW_MUTATION = """
mutation($pullRequestId: ID!) {
  markPullRequestReadyForReview(input: {pullRequestId: $pullRequestId}) {
    pullRequest {
      id
      number
      isDraft
      state
      url
    }
  }
}
"""

# GraphQL mutation to request Copilot code review on a PR
REQUEST_COPILOT_REVIEW_MUTATION = """
mutation($pullRequestId: ID!) {
  requestReviewsByLogin(input: {pullRequestId: $pullRequestId, botLogins: ["copilot"]}) {
    pullRequest {
      id
      number
      url
    }
  }
}
"""

# GraphQL mutation to merge a pull request into its base branch
# Used to merge child PR branches into the parent/main branch for an issue
MERGE_PULL_REQUEST_MUTATION = """
mutation($pullRequestId: ID!, $commitHeadline: String, $mergeMethod: PullRequestMergeMethod) {
  mergePullRequest(input: {
    pullRequestId: $pullRequestId,
    commitHeadline: $commitHeadline,
    mergeMethod: $mergeMethod
  }) {
    pullRequest {
      id
      number
      state
      merged
      mergedAt
      mergeCommit {
        oid
      }
      url
    }
  }
}
"""

# GraphQL query to get PR details by number (with commit status for completion detection)
GET_PULL_REQUEST_QUERY = """
query($owner: String!, $name: String!, $number: Int!) {
  repository(owner: $owner, name: $name) {
    pullRequest(number: $number) {
      id
      number
      title
      body
      state
      isDraft
      url
      headRefName
      baseRefName
      author {
        login
      }
      reviewRequests(first: 10) {
        nodes {
          requestedReviewer {
            ... on User {
              login
            }
          }
        }
      }
      reviews(first: 50) {
        nodes {
          author {
            login
          }
          state
          body
          createdAt
        }
      }
      commits(last: 1) {
        nodes {
          commit {
            oid
            committedDate
            statusCheckRollup {
              state
            }
          }
        }
      }
      createdAt
      updatedAt
    }
  }
}
"""

# Query to get all project fields (for setting metadata like Priority, Size, Estimate, dates)
GET_PROJECT_FIELDS_QUERY = """
query($projectId: ID!) {
  node(id: $projectId) {
    ... on ProjectV2 {
      fields(first: 50) {
        nodes {
          ... on ProjectV2Field {
            id
            name
            dataType
          }
          ... on ProjectV2SingleSelectField {
            id
            name
            dataType
            options {
              id
              name
            }
          }
          ... on ProjectV2IterationField {
            id
            name
            dataType
          }
        }
      }
    }
  }
}
"""

# Mutation to update a single select field value (Priority, Size, Status)
UPDATE_SINGLE_SELECT_FIELD_MUTATION = """
mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $optionId: String!) {
  updateProjectV2ItemFieldValue(
    input: {
      projectId: $projectId
      itemId: $itemId
      fieldId: $fieldId
      value: { singleSelectOptionId: $optionId }
    }
  ) {
    projectV2Item {
      id
    }
  }
}
"""

# Mutation to update a number field value (Estimate)
UPDATE_NUMBER_FIELD_MUTATION = """
mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $number: Float!) {
  updateProjectV2ItemFieldValue(
    input: {
      projectId: $projectId
      itemId: $itemId
      fieldId: $fieldId
      value: { number: $number }
    }
  ) {
    projectV2Item {
      id
    }
  }
}
"""

# Mutation to update a date field value (Start date, Target date)
UPDATE_DATE_FIELD_MUTATION = """
mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $date: Date!) {
  updateProjectV2ItemFieldValue(
    input: {
      projectId: $projectId
      itemId: $itemId
      fieldId: $fieldId
      value: { date: $date }
    }
  ) {
    projectV2Item {
      id
    }
  }
}
"""

# Mutation to update a text field value
UPDATE_TEXT_FIELD_MUTATION = """
mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $text: String!) {
  updateProjectV2ItemFieldValue(
    input: {
      projectId: $projectId
      itemId: $itemId
      fieldId: $fieldId
      value: { text: $text }
    }
  ) {
    projectV2Item {
      id
    }
  }
}
"""


# ──────────────────────────────────────────────────────────────────
# Board feature: GraphQL queries for project board display
# ──────────────────────────────────────────────────────────────────

# Query to list projects with full status field options (colors, descriptions)
BOARD_LIST_PROJECTS_QUERY = """
query($login: String!, $first: Int!) {
  user(login: $login) {
    projectsV2(first: $first) {
      nodes {
        id
        title
        url
        shortDescription
        closed
        field(name: "Status") {
          ... on ProjectV2SingleSelectField {
            id
            options {
              id
              name
              color
              description
            }
          }
        }
      }
    }
  }
}
"""

# Query to get all project items with custom field values for board display
BOARD_GET_PROJECT_ITEMS_QUERY = """
query($projectId: ID!, $first: Int!, $after: String) {
  node(id: $projectId) {
    ... on ProjectV2 {
      title
      url
      shortDescription
      owner {
        ... on User { login }
        ... on Organization { login }
      }
      field(name: "Status") {
        ... on ProjectV2SingleSelectField {
          id
          options {
            id
            name
            color
            description
          }
        }
      }
      items(first: $first, after: $after) {
        pageInfo {
          hasNextPage
          endCursor
        }
        nodes {
          id
          fieldValues(first: 20) {
            nodes {
              ... on ProjectV2ItemFieldSingleSelectValue {
                name
                optionId
                field { ... on ProjectV2FieldCommon { name } }
                color
              }
              ... on ProjectV2ItemFieldNumberValue {
                number
                field { ... on ProjectV2FieldCommon { name } }
              }
            }
          }
          content {
            ... on DraftIssue {
              title
              body
            }
            ... on Issue {
              id
              number
              title
              body
              url
              assignees(first: 10) {
                nodes {
                  login
                  avatarUrl
                }
              }
              repository {
                owner { login }
                name
              }
              timelineItems(itemTypes: [CONNECTED_EVENT, CROSS_REFERENCED_EVENT], first: 50) {
                nodes {
                  ... on ConnectedEvent {
                    subject {
                      ... on PullRequest {
                        id
                        number
                        title
                        state
                        url
                      }
                    }
                  }
                  ... on CrossReferencedEvent {
                    source {
                      ... on PullRequest {
                        id
                        number
                        title
                        state
                        url
                      }
                    }
                  }
                }
              }
            }
            ... on PullRequest {
              id
              number
              title
              body
              url
              state
              assignees(first: 10) {
                nodes {
                  login
                  avatarUrl
                }
              }
              repository {
                owner { login }
                name
              }
            }
          }
        }
      }
    }
  }
}
"""

