# infrastructure/terraform/modules/agent-runtime/cloud-run.tf

resource "google_cloud_run_service" "agent" {
  name     = var.agent_name
  location = var.region

  template {
    spec {
      containers {
        image = var.container_image
        
        resources {
          limits = {
            cpu    = var.cpu
            memory = var.memory
          }
        }
        
        env {
          name  = "AGENT_REGISTRY_URL"
          value = var.registry_url
        }
        
        env {
          name = "GCP_PROJECT"
          value = var.project_id
        }
      }
      
      service_account_name = google_service_account.agent.email
    }
    
    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale" = var.min_instances
        "autoscaling.knative.dev/maxScale" = var.max_instances
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }
}

resource "google_service_account" "agent" {
  account_id   = "${var.agent_name}-sa"
  display_name = "Service Account for ${var.agent_name}"
}

resource "google_cloud_run_service_iam_member" "invoker" {
  service  = google_cloud_run_service.agent.name
  location = google_cloud_run_service.agent.location
  role     = "roles/run.invoker"
  member   = "serviceAccount:${var.api_gateway_sa}"
}

# Register in Firestore
resource "google_firestore_document" "agent_registration" {
  collection  = "agents"
  document_id = var.agent_name
  
  fields = jsonencode({
    metadata = {
      name        = var.agent_name
      version     = var.agent_version
      description = var.description
    }
    endpoint = google_cloud_run_service.agent.status[0].url
    deployment = {
      target = "cloud-run"
      region = var.region
    }
    status = "active"
  })
}