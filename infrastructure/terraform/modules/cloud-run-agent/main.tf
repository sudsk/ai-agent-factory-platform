# Terraform module for deploying agents to Cloud Run

variable "agent_name" {
  description = "Name of the agent"
  type        = string
}

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "container_image" {
  description = "Container image URI"
  type        = string
}

variable "cpu" {
  description = "CPU allocation"
  type        = string
  default     = "2"
}

variable "memory" {
  description = "Memory allocation"
  type        = string
  default     = "4Gi"
}

variable "min_instances" {
  description = "Minimum number of instances"
  type        = number
  default     = 0
}

variable "max_instances" {
  description = "Maximum number of instances"
  type        = number
  default     = 10
}

variable "timeout" {
  description = "Request timeout in seconds"
  type        = number
  default     = 300
}

variable "concurrency" {
  description = "Maximum concurrent requests per instance"
  type        = number
  default     = 80
}

variable "env_vars" {
  description = "Environment variables"
  type        = map(string)
  default     = {}
}

variable "service_account_email" {
  description = "Service account email for the agent"
  type        = string
}

variable "allow_unauthenticated" {
  description = "Allow unauthenticated requests"
  type        = bool
  default     = false
}

# Cloud Run service
resource "google_cloud_run_v2_service" "agent" {
  name     = var.agent_name
  location = var.region
  project  = var.project_id
  
  template {
    service_account = var.service_account_email
    
    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }
    
    timeout = "${var.timeout}s"
    
    containers {
      image = var.container_image
      
      resources {
        limits = {
          cpu    = var.cpu
          memory = var.memory
        }
      }
      
      dynamic "env" {
        for_each = var.env_vars
        content {
          name  = env.key
          value = env.value
        }
      }
      
      # Health check
      startup_probe {
        http_get {
          path = "/health"
        }
        initial_delay_seconds = 10
        timeout_seconds      = 3
        period_seconds       = 10
        failure_threshold    = 3
      }
      
      liveness_probe {
        http_get {
          path = "/health"
        }
        initial_delay_seconds = 30
        timeout_seconds      = 3
        period_seconds       = 30
        failure_threshold    = 3
      }
    }
    
    # Container concurrency
    max_instance_request_concurrency = var.concurrency
  }
  
  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}

# IAM policy for public access (if enabled)
resource "google_cloud_run_v2_service_iam_member" "public_access" {
  count = var.allow_unauthenticated ? 1 : 0
  
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.agent.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Register agent in Firestore
resource "google_firestore_document" "agent_registration" {
  project     = var.project_id
  database    = "(default)"
  collection  = "agents"
  document_id = var.agent_name
  
  fields = jsonencode({
    metadata = {
      mapValue = {
        fields = {
          name = { stringValue = var.agent_name }
          registered_at = { timestampValue = timestamp() }
        }
      }
    }
    deployment = {
      mapValue = {
        fields = {
          target = { stringValue = "cloud-run" }
          region = { stringValue = var.region }
          endpoint = { stringValue = google_cloud_run_v2_service.agent.uri }
        }
      }
    }
    status = { stringValue = "active" }
  })
}

# Outputs
output "service_url" {
  description = "URL of the deployed Cloud Run service"
  value       = google_cloud_run_v2_service.agent.uri
}

output "service_name" {
  description = "Name of the Cloud Run service"
  value       = google_cloud_run_v2_service.agent.name
}
