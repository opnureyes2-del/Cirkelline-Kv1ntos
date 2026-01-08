// ArXiv Research Adapter
// Searches academic papers from arXiv.org

use crate::commander::{ResearchFinding, ResearchSource};
use crate::research::traits::{ResearchAdapter, ResearchError, ResearchResult, SearchOptions, SortOrder};
use async_trait::async_trait;
use chrono::{DateTime, Utc, NaiveDateTime};
use serde::Deserialize;

/// ArXiv API uses Atom XML, but we'll parse key fields
/// ArXiv API response entry
#[derive(Debug)]
struct ArXivEntry {
    id: String,
    title: String,
    summary: String,
    authors: Vec<String>,
    published: String,
    updated: String,
    categories: Vec<String>,
    link: String,
}

/// ArXiv Research Adapter
#[derive(Debug)]
pub struct ArXivAdapter {
    client: reqwest::Client,
    base_url: String,
}

impl ArXivAdapter {
    /// Create a new ArXiv adapter
    pub fn new() -> Self {
        let client = reqwest::Client::builder()
            .user_agent("CLA-ResearchAdapter/1.0")
            .timeout(std::time::Duration::from_secs(30))
            .build()
            .expect("Failed to create HTTP client");

        Self {
            client,
            base_url: "http://export.arxiv.org/api/query".to_string(),
        }
    }

    /// Parse arXiv Atom XML response (simplified parsing)
    fn parse_atom_response(xml: &str) -> Result<Vec<ArXivEntry>, String> {
        let mut entries = Vec::new();

        // Split by <entry> tags
        let entry_parts: Vec<&str> = xml.split("<entry>").skip(1).collect();

        for entry_xml in entry_parts {
            let entry_end = entry_xml.find("</entry>").unwrap_or(entry_xml.len());
            let entry_content = &entry_xml[..entry_end];

            // Parse ID
            let id = Self::extract_tag(entry_content, "id")
                .unwrap_or_else(|| uuid::Uuid::new_v4().to_string());

            // Parse title (remove newlines and extra whitespace)
            let title = Self::extract_tag(entry_content, "title")
                .map(|t| t.split_whitespace().collect::<Vec<_>>().join(" "))
                .unwrap_or_else(|| "Untitled".to_string());

            // Parse summary/abstract
            let summary = Self::extract_tag(entry_content, "summary")
                .map(|s| s.split_whitespace().collect::<Vec<_>>().join(" "))
                .unwrap_or_default();

            // Parse authors (simplified - just gets names)
            let mut authors = Vec::new();
            for author_section in entry_content.split("<author>").skip(1) {
                if let Some(name) = Self::extract_tag(author_section, "name") {
                    authors.push(name);
                }
            }

            // Parse dates
            let published = Self::extract_tag(entry_content, "published")
                .unwrap_or_else(|| Utc::now().to_rfc3339());
            let updated = Self::extract_tag(entry_content, "updated")
                .unwrap_or_else(|| published.clone());

            // Parse categories
            let mut categories = Vec::new();
            for cat_match in entry_content.match_indices("category term=\"") {
                let start = cat_match.0 + "category term=\"".len();
                if let Some(end) = entry_content[start..].find('"') {
                    categories.push(entry_content[start..start + end].to_string());
                }
            }

            // Get PDF link
            let link = Self::extract_link(entry_content)
                .unwrap_or_else(|| format!("https://arxiv.org/abs/{}", id.split('/').last().unwrap_or(&id)));

            entries.push(ArXivEntry {
                id,
                title,
                summary,
                authors,
                published,
                updated,
                categories,
                link,
            });
        }

        Ok(entries)
    }

    /// Extract content from XML tag
    fn extract_tag(xml: &str, tag: &str) -> Option<String> {
        let start_tag = format!("<{}>", tag);
        let end_tag = format!("</{}>", tag);

        let start = xml.find(&start_tag)?;
        let content_start = start + start_tag.len();
        let end = xml[content_start..].find(&end_tag)?;

        Some(xml[content_start..content_start + end].trim().to_string())
    }

    /// Extract link from entry
    fn extract_link(xml: &str) -> Option<String> {
        // Look for the abstract page link
        for link_match in xml.match_indices("href=\"") {
            let start = link_match.0 + "href=\"".len();
            if let Some(end) = xml[start..].find('"') {
                let href = &xml[start..start + end];
                if href.contains("arxiv.org/abs/") {
                    return Some(href.to_string());
                }
            }
        }
        None
    }

    /// Calculate relevance score for arXiv paper
    fn calculate_relevance(entry: &ArXivEntry, query: &str) -> f32 {
        let mut score = 0.3; // Base score for being a result
        let query_lower = query.to_lowercase();
        let query_terms: Vec<&str> = query_lower.split_whitespace().collect();

        // Title match (most important)
        let title_lower = entry.title.to_lowercase();
        for term in &query_terms {
            if title_lower.contains(term) {
                score += 0.15;
            }
        }
        // Exact phrase match in title
        if title_lower.contains(&query_lower) {
            score += 0.2;
        }

        // Summary/abstract match
        let summary_lower = entry.summary.to_lowercase();
        let summary_matches = query_terms
            .iter()
            .filter(|term| summary_lower.contains(*term))
            .count();
        score += (summary_matches as f32 * 0.05).min(0.2);

        // Recent papers get bonus
        if let Ok(published) = Self::parse_arxiv_date(&entry.published) {
            let days_ago = (Utc::now() - published).num_days();
            if days_ago < 30 {
                score += 0.15;
            } else if days_ago < 90 {
                score += 0.08;
            } else if days_ago < 365 {
                score += 0.03;
            }
        }

        // Category relevance (AI/ML categories get bonus for tech queries)
        let ai_categories = ["cs.AI", "cs.LG", "cs.CL", "cs.CV", "stat.ML"];
        if entry.categories.iter().any(|c| ai_categories.contains(&c.as_str())) {
            if query_lower.contains("ai") || query_lower.contains("machine learning")
               || query_lower.contains("neural") || query_lower.contains("deep learning") {
                score += 0.1;
            }
        }

        score.min(1.0).max(0.0)
    }

    /// Parse arXiv date format
    fn parse_arxiv_date(date_str: &str) -> Result<DateTime<Utc>, ()> {
        // ArXiv uses ISO 8601 format like "2024-01-15T12:00:00Z"
        DateTime::parse_from_rfc3339(date_str)
            .map(|dt| dt.with_timezone(&Utc))
            .map_err(|_| ())
    }

    /// Convert ArXiv entry to ResearchFinding
    fn entry_to_finding(entry: ArXivEntry, query: &str) -> ResearchFinding {
        let relevance_score = Self::calculate_relevance(&entry, query);

        let discovered_at = Self::parse_arxiv_date(&entry.updated)
            .or_else(|_| Self::parse_arxiv_date(&entry.published))
            .unwrap_or_else(|_| Utc::now());

        let mut tags = entry.categories.clone();
        tags.push("arxiv".to_string());
        tags.push("academic".to_string());

        let authors_str = if entry.authors.len() > 3 {
            format!("{} et al.", entry.authors[0])
        } else {
            entry.authors.join(", ")
        };

        // Create summary with authors
        let summary = format!(
            "Authors: {}\n\n{}",
            authors_str,
            if entry.summary.len() > 500 {
                format!("{}...", &entry.summary[..500])
            } else {
                entry.summary.clone()
            }
        );

        ResearchFinding {
            id: format!("arxiv-{}", entry.id.split('/').last().unwrap_or(&entry.id)),
            source: ResearchSource::ArXiv,
            title: entry.title,
            summary,
            relevance_score,
            discovered_at,
            tags,
            url: Some(entry.link),
            metadata: serde_json::json!({
                "authors": entry.authors,
                "categories": entry.categories,
                "published": entry.published,
                "updated": entry.updated,
            }),
        }
    }

    /// Build arXiv sort parameter
    fn build_sort_param(sort: &Option<SortOrder>) -> &str {
        match sort {
            Some(SortOrder::DateDesc) => "submittedDate",
            Some(SortOrder::DateAsc) => "submittedDate",
            Some(SortOrder::PopularityDesc) => "relevance", // ArXiv doesn't have popularity
            _ => "relevance",
        }
    }
}

impl Default for ArXivAdapter {
    fn default() -> Self {
        Self::new()
    }
}

#[async_trait]
impl ResearchAdapter for ArXivAdapter {
    fn name(&self) -> &str {
        "ArXiv"
    }

    fn source(&self) -> ResearchSource {
        ResearchSource::ArXiv
    }

    async fn validate(&self) -> ResearchResult<()> {
        // Test with a simple query
        let url = format!("{}?search_query=all:test&max_results=1", self.base_url);

        match self.client.get(&url).send().await {
            Ok(response) => {
                if response.status().is_success() {
                    Ok(())
                } else {
                    Err(ResearchError::ApiError {
                        status: response.status().as_u16(),
                        message: "ArXiv API unavailable".to_string(),
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
        let sort_by = Self::build_sort_param(&options.sort_by);
        let sort_order = match options.sort_by {
            Some(SortOrder::DateAsc) => "ascending",
            _ => "descending",
        };

        // URL encode the query
        let encoded_query = query
            .replace(' ', "+AND+")
            .replace(':', "%3A");

        // Build arXiv API URL
        // search_query format: all:query or ti:title or abs:abstract
        let url = format!(
            "{}?search_query=all:{}&max_results={}&sortBy={}&sortOrder={}",
            self.base_url, encoded_query, limit, sort_by, sort_order
        );

        log::debug!("ArXiv API URL: {}", url);

        let response = self.client.get(&url).send().await.map_err(|e| {
            ResearchError::NetworkError(format!("ArXiv API request failed: {}", e))
        })?;

        if !response.status().is_success() {
            let status = response.status().as_u16();
            let text = response.text().await.unwrap_or_default();
            return Err(ResearchError::ApiError {
                status,
                message: text,
            });
        }

        let xml_response = response.text().await.map_err(|e| {
            ResearchError::ParseError(format!("Failed to read ArXiv response: {}", e))
        })?;

        let entries = Self::parse_atom_response(&xml_response).map_err(|e| {
            ResearchError::ParseError(format!("Failed to parse ArXiv XML: {}", e))
        })?;

        log::info!("ArXiv search returned {} results", entries.len());

        let mut findings: Vec<ResearchFinding> = entries
            .into_iter()
            .map(|entry| Self::entry_to_finding(entry, query))
            .collect();

        // Filter by minimum relevance if specified
        if let Some(min_rel) = options.min_relevance {
            findings.retain(|f| f.relevance_score >= min_rel);
        }

        // Filter by date if specified
        if let Some(since) = options.since_timestamp {
            let since_dt = DateTime::from_timestamp(since, 0).unwrap_or_else(|| Utc::now());
            findings.retain(|f| f.discovered_at >= since_dt);
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
        // Get recent AI/ML papers
        self.search(
            "cat:cs.AI OR cat:cs.LG OR cat:cs.CL",
            &SearchOptions {
                limit: Some(limit),
                sort_by: Some(SortOrder::DateDesc),
                ..Default::default()
            },
        )
        .await
    }
}
