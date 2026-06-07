# GitOps deployment repository

This directory is intended to be the root of the **deployment configuration repository**. Argo CD
reads this repository; application CI writes only the immutable image tag in
`environments/prod-values.yaml`.

Before bootstrapping:

1. Replace the image repository in the environment values files.
2. Replace `REPLACE_ORG` in `argocd/application.yaml`.
3. If this is a private repository, configure an Argo CD repository credential secret.
4. Commit and push to the protected `main` branch.

The Argo CD application enables automated sync, pruning, and self-healing. Therefore, direct
changes made with `kubectl` are reverted to the state declared here.
