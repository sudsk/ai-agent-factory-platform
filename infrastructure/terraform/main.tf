# Main Terraform configuration for AI Agent Factory Platform

terraform {
  required_version = ">= 1.5"
  
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
  
  backend "gcs" {
    bucket = "agent-factory-terraform-state"
    prefix = "terraform/state"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "run.googleapis.com",
    "cloudbuild.googleapis.com",
    "artifactregistry.googleapis.com",
    "firestore.googleapis.com",
    "aiplatform.googleapis.com",
    "compute.googleapis.com",
    "container.googleapis.com",
    "pubsub.googleapis.com",
    "monitoring.googleapis.com",
    "logging.googleapis.com",
    "dlp.googleapis.com",
    "secretmanager.googleapis.com",
  ])
  
  project = var.project_id
  service = each.value
  
  disable_on_destroy = false
}

# Firestore database for Agent Registry
resource "google_firestore_database" "agent_registry" {
  project     = var.project_id
  name        = "(default)"
  location_id = var.region
  type        = "FIRESTORE_NATIVE"
  
  depends_on = [google_project_service.required_apis]
}

# Pub/Sub topics for async agent communication
resource "google_pubsub_topic" "agent_events" {
  name = "agent-events"
  
  message_retention_duration = "604800s"  # 7 days
  
  depends_on = [google_project_service.required_apis]
}

# Cloud Storage buckets
resource "google_storage_bucket" "agent_artifacts" {
  name          = "${var.project_id}-agent-artifacts"
  location      = var.region
  force_destroy = false
  
  uniform_bucket_level_access = true
  
  versioning {
    enabled = true
  }
  
  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }
}

resource "google_storage_bucket" "terraform_state" {
  name          = "${var.project_id}-terraform-state"
  location      = var.region
  force_destroy = false
  
  uniform_bucket_level_access = true
  
  versioning {
    enabled = true
  }
}

# BigQuery dataset for analytics
resource "google_bigquery_dataset" "agent_analytics" {
  dataset_id  = "agent_analytics"
  location    = var.region
  description = "Analytics data for AI Agent Factory"
  
  default_table_expiration_ms = 7776000000  # 90 days
  
  depends_on = [google_project_service.required_apis]
}

# BigQuery tables
resource "google_bigquery_table" "agent_invocations" {
  dataset_id = google_bigquery_dataset.agent_analytics.dataset_id
  table_id   = "agent_invocations"
  
  schema = jsonencode([
    {
      name = "timestamp"
      type = "TIMESTAMP"
      mode = "REQUIRED"
    },
    {
      name = "agent_name"
      type = "STRING"
      mode = "REQUIRED"
    },
    {
      name = "duration_ms"
      type = "INTEGER"
      mode = "REQUIRED"
    },
    {
      name = "success"
      type = "BOOLEAN"
      mode = "REQUIRED"
    },
    {
      name = "error_message"
      type = "STRING"
      mode = "NULLABLE"
    },
    {
      name = "user_id"
      type = "STRING"
      mode = "NULLABLE"
    }
  ])
  
  time_partitioning {
    type  = "DAY"
    field = "timestamp"
  }
}

resource "google_bigquery_table" "agent_costs" {
  dataset_id = google_bigquery_dataset.agent_analytics.dataset_id
  table_id   = "agent_costs"
  
  schema = jsonencode([
    {
      name = "timestamp"
      type = "TIMESTAMP"
      mode = "REQUIRED"
    },
    {
      name = "agent_name"
      type = "STRING"
      mode = "REQUIRED"
    },
    {
      name = "cost_usd"
      type = "FLOAT"
      mode = "REQUIRED"
    },
    {
      name = "tokens_used"
      type = "INTEGER"
      mode = "NULLABLE"
    },
    {
      name = "deployment_target"
      type = "STRING"
      mode = "NULLABLE"
    }
  ])
  
  time_partitioning {
    type  = "DAY"
    field = "timestamp"
  }
}

# VPC for agent networking
resource "google_compute_network" "agent_vpc" {
  name                    = "agent-factory-vpc"
  auto_create_subnetworks = false
  
  depends_on = [google_project_service.required_apis]
}

resource "google_compute_subnetwork" "agent_subnet" {
  name          = "agent-factory-subnet"
  ip_cidr_range = "10.0.0.0/24"
  region        = var.region
  network       = google_compute_network.agent_vpc.id
  
  private_ip_google_access = true
}

# Cloud Armor security policy
resource "google_compute_security_policy" "api_security" {
  name = "agent-factory-api-security"
  
  # Rate limiting rule
  rule {
    action   = "rate_based_ban"
    priority = "100"
    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = ["*"]
      }
    }
    rate_limit_options {
      conform_action = "allow"
      exceed_action  = "deny(429)"
      
      rate_limit_threshold {
        count        = 100
        interval_sec = 60
      }
      
      ban_duration_sec = 600
    }
  }
  
  # Default rule
  rule {
    action   = "allow"
    priority = "2147483647"
    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = ["*"]
      }
    }
  }
}

# Service accounts
resource "google_service_account" "agent_registry_sa" {
  account_id   = "agent-registry-sa"
  display_name = "Agent Registry Service Account"
}

resource "google_service_account" "agent_runtime_sa" {
  account_id   = "agent-runtime-sa"
  display_name = "Agent Runtime Service Account"
}

# IAM bindings for Agent Registry
resource "google_project_iam_member" "registry_firestore" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.agent_registry_sa.email}"
}

resource "google_project_iam_member" "registry_logging" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.agent_registry_sa.email}"
}

# IAM bindings for Agent Runtime
resource "google_project_iam_member" "runtime_firestore" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.agent_runtime_sa.email}"
}

resource "google_project_iam_member" "runtime_vertex" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.agent_runtime_sa.email}"
}

resource "google_project_iam_member" "runtime_pubsub" {
  project = var.project_id
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:${google_service_account.agent_runtime_sa.email}"
}

resource "google_project_iam_member" "runtime_storage" {
  project = var.project_id
  role    = "roles/storage.objectViewer"
  member  = "serviceAccount:${google_service_account.agent_runtime_sa.email}"
}

resource "google_project_iam_member" "runtime_monitoring" {
  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.agent_runtime_sa.email}"
}

# Monitoring notification channel
resource "google_monitoring_notification_channel" "email" {
  display_name = "Agent Factory Alerts"
  type         = "email"
  
  labels = {
    email_address = var.alert_email
  }
}

# Alert policies
resource "google_monitoring_alert_policy" "high_error_rate" {
  display_name = "High Agent Error Rate"
  combiner     = "OR"
  
  conditions {
    display_name = "Agent error rate > 5%"
    
    condition_threshold {
      filter          = "resource.type = \"cloud_run_revision\" AND metric.type = \"run.googleapis.com/request_count\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 0.05
      
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }
  
  notification_channels = [google_monitoring_notification_channel.email.id]
  
  alert_strategy {
    auto_close = "604800s"  # 7 days
  }
}

# Outputs
output "project_id" {
  value = var.project_id
}

output "region" {
  value = var.region
}

output "agent_registry_sa_email" {
  value = google_service_account.agent_registry_sa.email
}

output "agent_runtime_sa_email" {
  value = google_service_account.agent_runtime_sa.email
}

output "vpc_name" {
  value = google_compute_network.agent_vpc.name
}

output "subnet_name" {
  value = google_compute_subnetwork.agent_subnet.name
}
