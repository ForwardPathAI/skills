# Azure Ops Playbooks

Symptom → checks, in order. Commands are in [SKILL.md](SKILL.md#inspect). Stop at the first check that explains the symptom, confirm it with evidence, and report. A playbook is done when one cause has quoted evidence, or every check ran clean and you say so.

## New revision never becomes ready

`latestRevisionName` ≠ `latestReadyRevisionName`, or the revision shows `Failed` / `Unhealthy`.

1. **System logs** for that revision (`--type system --revision <rev>`). The `Reason_s` names the stage:
   - `ImagePullBackOff`, `ErrImagePull`, `PullImageFailed` → **image pull** below.
   - `ContainerCrashing`, `ContainerTerminated`, `BackOff` → **crash loop** below.
   - `ProbeFailed` → **probes** below.
2. **Image pull.**
   - The image exists in `forwardpathai`: for a tag reference, `show-tags`; for an `@sha256:` reference, `az acr manifest show-metadata -r forwardpathai -n <repo>@<digest>`?
   - The app's registry entry uses an identity, and that identity is attached to the app?
   - The identity holds `AcrPull` or `Container Registry Repository Reader` on the registry (`role assignment list`)?
   - Customer-tenant apps: the pull token's scope map lists this repository and the token has not expired.
3. **Crash loop.** Console logs for the revision. Look for the first error after start: missing env var, failed migration, bad connection string, port already bound. Compare env var names against the previous ready revision.
4. **Probes.** Ingress `targetPort` matches the port the app listens on (check the Dockerfile `EXPOSE` and the app's `PORT`). Probe paths return 200 without auth. A slow start needs a longer startup probe, not a disabled one.

## App was working, now 5xx or unreachable

1. **Revision health and replicas.** Zero running replicas with scale-to-zero is normal; the first request cold-starts. Zero replicas with a `minReplicas` above zero is a failure: go to the crash-loop check above.
2. **Recent change.** Compare `createdTime` of the active revision with when errors started (`ContainerAppConsoleLogs_CL` time series). A match points to the deploy; roll back traffic after approval.
3. **App errors.** Console logs and App Insights `exceptions` / `requests | where success == false` over the incident window.
4. **Dependencies.** App Insights `dependencies | where success == false` shows which downstream (Postgres, Redis, OpenAI, an external API) is failing. Continue with the matching section.
5. **Ingress and domain.** Ingress `external` is true for public apps; the custom domain binding and managed certificate show `Succeeded`; DNS CNAME still points at the app FQDN.

## Database connection fails

1. Server `state` is `Ready` (not `Stopped` — dev servers are sometimes stopped to save cost).
2. **Network path.** Private access: the Container Apps environment sits on the VNet the private endpoint and private DNS zone link to. Public access: consumption environments egress from a large, shifting pool of IPs (`properties.outboundIpAddresses` on the app lists 100+), so per-IP firewall rules break without warning. Report that as the cause and point to private networking per [azure-conventions](../azure-conventions/SECURITY.md#network) rather than widening the firewall.
3. **TLS.** The client connects with `sslmode=require` or stricter.
4. **Credentials.** The connection-string secret resolves (next section). Entra-auth servers: the app identity exists as a Postgres role.

## Key Vault reference does not resolve

Symptoms: secret-backed env var empty, revision fails with a secret error, or system logs show `SecretRef` / Key Vault failures.

1. `az containerapp secret list` shows the secret with a `keyVaultUrl` and the identity it uses.
2. The secret name in that URL exists and is enabled in the vault (`secret list`, names only).
3. The referenced identity holds `Key Vault Secrets User` on the vault or that secret.
4. The vault's network rules let the Container Apps environment through.

After fixing any of these, restart the revision (a write) so the app re-reads the secret.

## Job failed

1. `job execution list` for the failed execution's status and start time.
2. `job logs show --execution <name> --container <container>` for its output.
3. Migration jobs: the database checks above apply; also confirm the job runs the same image digest as the app it migrates for.
