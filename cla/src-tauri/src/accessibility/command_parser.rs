// Command Parser - Parses natural language voice commands
// Supports Danish and English commands

use serde::{Deserialize, Serialize};

/// Parsed voice command
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum VoiceCommand {
    /// Start the Commander Unit
    StartCommander,
    /// Stop the Commander Unit
    StopCommander,
    /// Get system status
    GetStatus,
    /// Search for something
    Search { query: String },
    /// Create a task
    CreateTask { description: String, priority: String },
    /// Read notifications
    ReadNotifications,
    /// Get help
    Help,
    /// Cancel current operation
    Cancel,
    /// Repeat last response
    Repeat,
    /// Unknown command
    Unknown(String),
}

/// Command Parser for natural language
pub struct CommandParser {
    language: String,
}

impl CommandParser {
    /// Create new parser
    pub fn new(language: &str) -> Self {
        Self {
            language: language.to_string(),
        }
    }

    /// Parse natural language text into a command
    pub async fn parse(&self, text: &str) -> VoiceCommand {
        let lower = text.to_lowercase().trim().to_string();

        // Danish commands
        if self.language.starts_with("da") {
            return self.parse_danish(&lower);
        }

        // English commands
        self.parse_english(&lower)
    }

    /// Parse Danish commands
    fn parse_danish(&self, text: &str) -> VoiceCommand {
        // Start commands
        if self.matches_any(text, &[
            "start", "begynd", "start arbejde", "begynd arbejde",
            "start commander", "aktiver", "kør", "sæt i gang"
        ]) {
            return VoiceCommand::StartCommander;
        }

        // Stop commands
        if self.matches_any(text, &[
            "stop", "stands", "stop arbejde", "stands arbejde",
            "stop commander", "deaktiver", "afslut", "hold pause"
        ]) {
            return VoiceCommand::StopCommander;
        }

        // Status commands
        if self.matches_any(text, &[
            "status", "hvad er status", "hvordan går det",
            "vis status", "hvad sker der", "rapport"
        ]) {
            return VoiceCommand::GetStatus;
        }

        // Search commands
        if let Some(query) = self.extract_after(text, &[
            "søg efter", "find", "søg", "led efter", "undersøg"
        ]) {
            return VoiceCommand::Search { query };
        }

        // Create task commands
        if let Some(description) = self.extract_after(text, &[
            "opret opgave", "ny opgave", "tilføj opgave",
            "lav en opgave", "skriv ned"
        ]) {
            let priority = if text.contains("vigtig") || text.contains("høj prioritet") {
                "high"
            } else if text.contains("kritisk") || text.contains("haster") {
                "critical"
            } else {
                "normal"
            };
            return VoiceCommand::CreateTask {
                description,
                priority: priority.to_string(),
            };
        }

        // Notifications
        if self.matches_any(text, &[
            "notifikationer", "læs notifikationer", "beskeder",
            "hvad er nyt", "nye beskeder", "ulæste"
        ]) {
            return VoiceCommand::ReadNotifications;
        }

        // Help
        if self.matches_any(text, &[
            "hjælp", "hvad kan du", "muligheder", "kommandoer",
            "hvad kan jeg sige", "vis hjælp"
        ]) {
            return VoiceCommand::Help;
        }

        // Cancel
        if self.matches_any(text, &[
            "annuller", "afbryd", "nej", "glem det", "fortryd"
        ]) {
            return VoiceCommand::Cancel;
        }

        // Repeat
        if self.matches_any(text, &[
            "gentag", "sig det igen", "hvad sagde du", "repeat",
            "en gang til", "igen"
        ]) {
            return VoiceCommand::Repeat;
        }

        VoiceCommand::Unknown(text.to_string())
    }

    /// Parse English commands
    fn parse_english(&self, text: &str) -> VoiceCommand {
        // Start commands
        if self.matches_any(text, &[
            "start", "begin", "start working", "begin working",
            "start commander", "activate", "run", "go"
        ]) {
            return VoiceCommand::StartCommander;
        }

        // Stop commands
        if self.matches_any(text, &[
            "stop", "halt", "stop working", "stop commander",
            "deactivate", "quit", "pause", "end"
        ]) {
            return VoiceCommand::StopCommander;
        }

        // Status commands
        if self.matches_any(text, &[
            "status", "what's the status", "how's it going",
            "show status", "what's happening", "report"
        ]) {
            return VoiceCommand::GetStatus;
        }

        // Search commands
        if let Some(query) = self.extract_after(text, &[
            "search for", "find", "search", "look for", "investigate"
        ]) {
            return VoiceCommand::Search { query };
        }

        // Create task commands
        if let Some(description) = self.extract_after(text, &[
            "create task", "new task", "add task",
            "make a task", "note down", "remember"
        ]) {
            let priority = if text.contains("important") || text.contains("high priority") {
                "high"
            } else if text.contains("critical") || text.contains("urgent") {
                "critical"
            } else {
                "normal"
            };
            return VoiceCommand::CreateTask {
                description,
                priority: priority.to_string(),
            };
        }

        // Notifications
        if self.matches_any(text, &[
            "notifications", "read notifications", "messages",
            "what's new", "new messages", "unread"
        ]) {
            return VoiceCommand::ReadNotifications;
        }

        // Help
        if self.matches_any(text, &[
            "help", "what can you do", "options", "commands",
            "what can i say", "show help"
        ]) {
            return VoiceCommand::Help;
        }

        // Cancel
        if self.matches_any(text, &[
            "cancel", "abort", "nevermind", "no", "forget it", "undo"
        ]) {
            return VoiceCommand::Cancel;
        }

        // Repeat
        if self.matches_any(text, &[
            "repeat", "say that again", "what did you say",
            "once more", "again", "pardon"
        ]) {
            return VoiceCommand::Repeat;
        }

        VoiceCommand::Unknown(text.to_string())
    }

    /// Check if text matches any of the patterns
    fn matches_any(&self, text: &str, patterns: &[&str]) -> bool {
        patterns.iter().any(|p| {
            text == *p || text.starts_with(&format!("{} ", p)) || text.contains(p)
        })
    }

    /// Extract text after matching prefix
    fn extract_after(&self, text: &str, prefixes: &[&str]) -> Option<String> {
        for prefix in prefixes {
            if let Some(rest) = text.strip_prefix(prefix) {
                let trimmed = rest.trim();
                if !trimmed.is_empty() {
                    return Some(trimmed.to_string());
                }
            }
            // Also check if prefix is contained
            if let Some(pos) = text.find(prefix) {
                let rest = &text[pos + prefix.len()..];
                let trimmed = rest.trim();
                if !trimmed.is_empty() {
                    return Some(trimmed.to_string());
                }
            }
        }
        None
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_danish_start_command() {
        let parser = CommandParser::new("da-DK");
        assert_eq!(parser.parse("start arbejde").await, VoiceCommand::StartCommander);
        assert_eq!(parser.parse("begynd").await, VoiceCommand::StartCommander);
    }

    #[tokio::test]
    async fn test_danish_search_command() {
        let parser = CommandParser::new("da-DK");
        match parser.parse("søg efter vejret i morgen").await {
            VoiceCommand::Search { query } => assert_eq!(query, "vejret i morgen"),
            _ => panic!("Expected Search command"),
        }
    }

    #[tokio::test]
    async fn test_english_help_command() {
        let parser = CommandParser::new("en-US");
        assert_eq!(parser.parse("help").await, VoiceCommand::Help);
        assert_eq!(parser.parse("what can you do").await, VoiceCommand::Help);
    }
}
