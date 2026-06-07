# Google Cloud infrastructure

The Terraform stack creates:

- a custom VPC and VPC-native subnet,
- a regional GKE cluster with exactly two worker nodes,
- a Docker Artifact Registry repository with cleanup policies,
- least-privilege service accounts for GKE nodes and CI, and
- GitHub OIDC Workload Identity Federation (no downloadable service-account key).

## Apply

```bash
gcloud auth application-default login
gcloud config set project PROJECT_ID
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars.
terraform init
terraform plan
terraform apply
```

Save the `github_service_account` and `workload_identity_provider` outputs as GitHub Actions
secrets, and the region, project, and Artifact Registry repository as Actions variables.
