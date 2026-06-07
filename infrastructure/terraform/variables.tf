variable "project_id" {
  description = "Google Cloud project ID."
  type        = string
}

variable "region" {
  description = "Region for GKE and Artifact Registry."
  type        = string
  default     = "us-central1"
}

variable "node_zone" {
  description = "Single zone used by the regional cluster worker pool so node_count is the total."
  type        = string
  default     = "us-central1-a"
}

variable "cluster_name" {
  description = "GKE cluster name."
  type        = string
  default     = "ml-platform"
}

variable "artifact_repository_id" {
  description = "Artifact Registry Docker repository ID."
  type        = string
  default     = "ml-images"
}

variable "node_machine_type" {
  description = "Machine type used by the two-node worker pool."
  type        = string
  default     = "e2-standard-2"
}

variable "github_repository" {
  description = "Application repository in owner/name format, used to restrict GitHub OIDC."
  type        = string
}
