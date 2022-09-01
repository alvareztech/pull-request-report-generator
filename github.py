API_BASE_URL = "https://api.github.com"
GRAPHQL_URL = "https://api.github.com/graphql"
TAG_GRAPHQL = """
{
  organization(login: "%s") {
    repository(name: "%s") {
      ref(qualifiedName: "refs/tags/%s") {
        name
        target {
          oid
          ... on Commit {
            id
            authoredDate
            committedDate
            associatedPullRequests(last: 10) {
              nodes {
                id
                number
                title
                createdAt
                mergedAt
                url
                body
              }
            }
          }
          ... on Tag {
            target {
              ... on Commit {
                id
                authoredDate
                committedDate
                associatedPullRequests(last: 10) {
                  nodes {
                    id
                    number
                    title
                    createdAt
                    mergedAt
                    url
                    body
                    author {
                      login
                      ... on User {
                        id
                        email
                        name
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
"""
PR_GRAPHQL = """
{
  repository(owner: "%s", name: "%s") {
    pullRequest(number: %d) {
      title
      createdAt
      mergedAt
      url
      body
      merged
      baseRefName
      author {
        login
        ... on User {
          id
          name
        }
      }
      mergedBy {
        login
        ... on User {
          id
          name
        }
      }
      mergeCommit {
        commitUrl
        oid
      }
      files(last: 10) {
        nodes {
          path
        }
      }
      reviews(first: 10, states: APPROVED) {
        nodes {
          author {
            login
            ... on User {
              id
              name
            }
          }
          state
          updatedAt
        }
      }
    }
  }
}
"""
