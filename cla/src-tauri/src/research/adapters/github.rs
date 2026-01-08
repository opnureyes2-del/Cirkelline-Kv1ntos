// GitHub Research Adapter
// Searches GitHub repositories, trending repos, and discussions

use crate::commander::{ResearchFinding, ResearchSource};
use crate::research::traits::{ResearchAdapter, ResearchError, ResearchResult, SearchOptions, SortOrder};
use async_trait::async_trait;
use chrono::{DateTime, Utc};
use serde::Deserialize;

/// GitHub API response structures
#[derive(Debug, Deserialize)]
struct GitHubSearchResponse {
    total_count: u32,
    incomplete_results: bool,
    items: Vec<GitHubRepo>,
}

#[derive(Debug, Deserialize)]
struct GitHubRepo {
    id: u64,
    name: String,
    full_name: String,
    description: Option<String>,
    html_url: String,
    stargazers_count: u32,
    forks_count: u32,
    language: Option<String>,
    topics: Vec<String>,
    created_at: String,
    updated_at: String,
    pushed_at: Option<String>,
}

/// GitHub Research Adapter
#[derive(Debug)]
pub struct GitHubAdapter {
    client: reqwest::Client,
    api_token: Option<String>,
    base_url: String,
}

impl GitHubAdapter {
    /// Create a new GitHub adapter
    pub fn new(api_token: Option<String>) -> Self {
        let client = reqwest::Client::builder()
            .user_agent("CLA-ResearchAdapter/1.0")
            .timeout(std::time::Duration::from_secs(30))
            .build()
            .expect("Failed to create HTTP client");

        Self {
            client,
            api_token,
            base_url: "https://api.github.com".to_string(),
        }
    }

    /// Build sort parameter for GitHub API
    fn build_sort_param(sort: &Option<SortOrder>) -> (&str, &str) {
        match sort {
            Some(SortOrder::DateDesc) | Some(SortOrder::DateAsc) => ("sort", "updated"),
            Some(SortOrder::PopularityDesc) => ("sort", "stars"),
            _ => ("sort", "best-match"),
        }
    }

    /// Calculate relevance score based on repo metrics
    fn calculate_relevance(repo: &GitHubRepo, query: &str) -> f32 {
        let mut score = 0.0;

        // Star count contributes to relevance
        let star_score = (repo.stargazers_count as f32).log10() / 5.0;
        score += star_score.min(0.3);

        // Description match
        if let Some(desc) = &repo.description {
            let query_lower = query.to_lowercase();
            let desc_lower = desc.to_lowercase();
            if desc_lower.contains(&query_lower) {
                score += 0.2;
            }
        }

        // Topic match
        let query_terms: Vec<&str> = query.split_whitespace().collect();
        for topic in &repo.topics {
            for term in &query_terms {
                if topic.to_lowercase().contains(&term.to_lowercase()) {
                    score += 0.1;
                }
            }
        }

        // Recent activity bonus
        if let Some(pushed) = &repo.pushed_at {
            if let Ok(pushed_date) = DateTime::parse_from_rfc3339(pushed) {
                let days_ago = (Utc::now() - pushed_date.with_timezone(&Utc)).num_days();
                if days_ago < 30 {
                    score += 0.2;
                } else if days_ago < 90 {
                    score += 0.1;
                }
            }
        }

        // Fork count indicates community interest
        if repo.forks_count > 100 {
            score += 0.1;
        }

        score.min(1.0).max(0.0)
    }

    /// Convert GitHub repo to ResearchFinding
    fn repo_to_finding(repo: GitHubRepo, query: &str) -> ResearchFinding {
        let relevance_score = Self::calculate_relevance(&repo, query);

        let discovered_at = DateTime::parse_from_rfc3339(&repo.updated_at)
            .map(|dt| dt.with_timezone(&Utc))
            .unwrap_or_else(|_| Utc::now());

        let mut tags = repo.topics.clone();
        if let Some(lang) = &repo.language {
            tags.push(format!("language:{}", lang.to_lowercase()));
        }
        tags.push("github".to_string());

        ResearchFinding {
            id: format!("github-{}", repo.id),
            source: ResearchSource::GitHub,
            title: repo.full_name,
            summary: repo.description.unwrap_or_else(|| "No description".to_string()),
            relevance_score,
            discovered_at,
            tags,
            url: Some(repo.html_url),
            metadata: serde_json::json!({
                "stars": repo.stargazers_count,
                "forks": repo.forks_count,
                "language": repo.language,
                "created_at": repo.created_at,
            }),
        }
    }
}

#[async_trait]
impl ResearchAdapter for GitHubAdapter {
    fn name(&self) -> &str {
        "GitHub"
    }

    fn source(&self) -> ResearchSource {
        ResearchSource::GitHub
    }

    async fn validate(&self) -> ResearchResult<()> {
        // Test API connectivity with rate limit endpoint
        let url = format!("{}/rate_limit", self.base_url);

        let mut request = self.client.get(&url);
        if let Some(token) = &self.api_token {
            request = request.header("Authorization", format!("Bearer {}", token));
        }

        match request.send().await {
            Ok(response) => {
                if response.status().is_success() {
                    Ok(())
                } else if response.status().as_u16() == 401 {
                    Err(ResearchError::ConfigError("Invalid GitHub token".to_string()))
                } else {
                    Err(ResearchError::ApiError {
                        status: response.status().as_u16(),
                        message: "GitHub API unavailable".to_string(),
                    })
                }
            }
            Err(e) => Err(ResearchError::NetworkError(e.to_string())),
        }
    }

    async fn search(
        &self,
        query: &str,
        options: &SearchOptions,
    ) -> ResearchResult<Vec<ResearchFinding>> {
        if query.trim().is_empty() {
            return Err(ResearchError::InvalidQuery("Query cannot be empty".to_string()));
        }

        let limit = options.limit.unwrap_or(10).min(100);
        let (sort_key, sort_value) = Self::build_sort_param(&options.sort_by);

        // Build query with date filter if specified
        let mut search_query = query.to_string();
        if let Some(timestamp) = options.since_timestamp {
            let date = DateTime::from_timestamp(timestamp, 0)
                .map(|dt| dt.format("%Y-%m-%d").to_string())
                .unwrap_or_default();
            if !date.is_empty() {
                search_query = format!("{} pushed:>{}", search_query, date);
            }
        }

        let url = format!(
            "{}/search/repositories?q={}&per_page={}&{sort_key}={sort_value}",
            self.base_url,
            urlencoding::encode(&search_query),
            limit,
            sort_key = sort_key,
            sort_value = sort_value
        );

        let mut request = self.client.get(&url);
        if let Some(token) = &self.api_token {
            request = request.header("Authorization", format!("Bearer {}", token));
        }
        request = request.header("Accept", "application/vnd.github.v3+json");

        let response = request.send().await.map_err(|e| {
            ResearchError::NetworkError(format!("GitHub API request failed: {}", e))
        })?;

        // Handle rate limiting
        if response.status().as_u16() == 403 {
            let retry_after = response
                .headers()
                .get("x-ratelimit-reset")
                .and_then(|v| v.to_str().ok())
                .and_then(|s| s.parse::<u64>().ok())
                .map(|reset| reset.saturating_sub(Utc::now().timestamp() as u64));

            return Err(ResearchError::RateLimited {
                retry_after_secs: retry_after,
            });
        }

        if !response.status().is_success() {
            let status = response.status().as_u16();
            let text = response.text().await.unwrap_or_default();
            return Err(ResearchError::ApiError {
                status,
                message: text,
            });
        }

        let search_result: GitHubSearchResponse = response.json().await.map_err(|e| {
            ResearchError::ParseError(format!("Failed to parse GitHub response: {}", e))
        })?;

        log::info!(
            "GitHub search returned {} results (total: {})",
            search_result.items.len(),
            search_result.total_count
        );

        let mut findings: Vec<ResearchFinding> = search_result
            .items
            .into_iter()
            .map(|repo| Self::repo_to_finding(repo, query))
            .collect();

        // Filter by minimum relevance if specified
        if let Some(min_rel) = options.min_relevance {
            findings.retain(|f| f.relevance_score >= min_rel);
        }

        // Sort by relevance
        findings.sort_by(|a, b| {
            b.relevance_score
                .partial_cmp(&a.relevance_score)
                .unwrap_or(std::cmp::Ordering::Equal)
        });

        Ok(findings)
    }

    async fn get_trending(&self, limit: usize) -> ResearchResult<Vec<ResearchFinding>> {
        // Search for repos created in the last week with high star counts
        let week_ago = (Utc::now() - chrono::Duration::days(7))
            .format("%Y-%m-%d")
            .to_string();

        let query = format!("created:>{} stars:>50", week_ago);

        self.search(
            &query,
            &SearchOptions {
                limit: Some(limit),
                sort_by: Some(SortOrder::PopularityDesc),
                ..Default::default()
            },
        )
        .await
    }
}

// URL encoding helper (minimal implementation)
mod urlencoding {
    pub fn encode(input: &str) -> String {
        let mut encoded = String::new();
        for byte in input.bytes() {
            match byte {
                b'A'..=b'Z' | b'a'..=b'z' | b'0'..=b'9' | b'-' | b'_' | b'.' | b'~' => {
                    encoded.push(byte as char);
                }
                b' ' => encoded.push('+'),
                _ => {
                    encoded.push('%');
                    encoded.push_str(&format!("{:02X}", byte));
                }
            }
        }
        encoded
    }
}
