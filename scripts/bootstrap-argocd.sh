#!/usr/bin/env bash
set -euo pipefail

CLUSTER_NAME=${CLUSTER_NAME:-ml-platform}
REGION=${REGION:-us-central1}
PROJECT_ID=${PROJECT_ID:?Set PROJECT_ID}
DEPLOYMENT_REPO_URL=${DEPLOYMENT_REPO_URL:?Set DEPLOYMENT_REPO_URL}
ARGOCD_CHART_VERSION=${ARGOCD_CHART_VERSION:-7.8.26}

command -v gcloud >/dev/null || { echo "gcloud is required" >&2; exit 1; }
command -v kubectl >/dev/null || { echo "kubectl is required" >&2; exit 1; }
command -v helm >/dev/null || { echo "helm is required" >&2; exit 1; }

gcloud container clusters get-credentials "${CLUSTER_NAME}" \
  --region "${REGION}" \
  --project "${PROJECT_ID}"

helm repo add argo https://argoproj.github.io/argo-helm
helm repo update argo
helm upgrade --install argocd argo/argo-cd \
  --namespace argocd \
  --create-namespace \
  --version "${ARGOCD_CHART_VERSION}" \
  --set configs.params.server\.insecure=false \
  --wait

sed "s#https://github.com/REPLACE_ORG/ml-platform-deploy.git#${DEPLOYMENT_REPO_URL}#" \
  deployment/argocd/application.yaml | kubectl apply -f -

kubectl wait --for=condition=Established crd/applications.argoproj.io --timeout=60s
echo "Argo CD is installed and the ml-api-production Application is registered."
