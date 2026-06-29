---
name: customer-deployment-package
description: Produce a customer deployment handoff package for a Forward Path custom app: customer-runnable infra, Notion instructions from the deployment template, and a Windows-safe zip. Use when the user asks for a customer deployment package, customer/external infra, deployment handoff, customer install/setup instructions, or exported deployment docs for a client.
---

# Customer Deployment Package

Forward Path builds custom AI software and hands customers a self-contained package to deploy it in **their own** cloud tenant. This skill turns a repo's **internal** infrastructure into an **external** handoff: sanitized Terraform/Bicep, setup instructions in Notion, a 1Password link for ACR image pull credentials, and placeholders for customer-owned third-party service secrets.

Customers are usually **Azure** customers and usually on **Windows**, so the final artifact must use a Windows-safe filename.

## Prerequisites

- Run from the **application repo** (the one with the internal `infra/` or `infrastructure/` folder).
- **Notion MCP** connected. Inspect available tools/params under the MCP descriptors before calling (search, retrieve page, create page in a database, etc.). Stop and tell the user if no Notion MCP is available.
- **1Password** share link for the Forward Path-provided ACR image pull credentials only (username/password for pulling images). Do not put secret values in the zip or in git.
- **azure-infra-setup** skill available — read [azure-infra-setup/SKILL.md](../azure-infra-setup/SKILL.md) for Forward Path Azure conventions (shared ACR, OIDC/RBAC, Key Vault, regions, Container Apps) when shaping the external infra.

Stop and report anything missing before proceeding.

## Fixed Notion references

| Purpose | Notion ID |
|---------|-----------|
| Sample template page (`Deployment Instructions - [App Name] - [Customer]`) | `36c92ad1579b81819801cfd3276fe396` |
| Target deployments database (save the filled page here) | `49466b35ef21421199f5acb7be5bf9e0` |

Always copy the **sample template page** structure — never invent your own section layout.

## Workflow

Copy this checklist and track progress:

```
- [ ] Step 1: Confirm target cloud + gather inputs
- [ ] Step 2: Locate internal infra
- [ ] Step 3: Build the external infra variant (Terraform + Bicep)
- [ ] Step 4: Fill the deployment instructions from the Notion template
- [ ] Step 5: Save the filled page into the Notion deployments database
- [ ] Step 6: Export the Notion page and assemble the customer folder
- [ ] Step 7: Zip with a Windows-safe name and deliver
```

### Step 1: Confirm target cloud + gather inputs

Default cloud is **Azure**, but **always confirm** the target cloud (Azure / AWS / GCP) before generating infra — the customer deploys into their own tenant. If it is not Azure, ask for the conventions to follow (this skill's defaults assume Azure).

Gather:
- **Customer name** and **App name** (used in titles and the zip filename).
- Cloud + tenant/subscription expectations.
- Which services ship as images (frontend, backend, workers, etc.) and their image references (e.g. `forwardpathai.azurecr.io/<app-image>`).
- The **1Password share link** for the ACR image pull username/password.
- Any customer-owned third-party services the app needs (for example OpenRouter, model providers, email/SMS providers, or payment processors). Document the required secret names and where the customer must create or provide those values; do **not** imply Forward Path provides them through 1Password.
- App version, if using versioned naming.

Complete this step when the target cloud is confirmed and every required input is either recorded or explicitly blocked on the user.

### Step 2: Locate internal infra

Find the internal infra (commonly `infra/`, `infrastructure/`, `terraform/`, or `bicep/`). Read it to understand resources, env vars, app registrations, secret names, and image references. This internal infra is the source of truth; the external variant is a **derivative**, not a copy.

Complete this step when the source infra has been found and the app's resources, identities, env vars, secret names, and image references have been inventoried.

### Step 3: Build the external infra variant

Create an external infra set the **customer** can run in their tenant. Keep it in a checked-in deployment handoff folder under `docs/deployments/<Sanitized-Customer>-<Sanitized-App>-Deployment-<YYYY-MM-DD>/infra/`, not mixed into the repo's internal infra and not under ignored build output such as `dist/`.

Include **both Terraform and Bicep** (unless the user scopes to one). Apply [azure-infra-setup](../azure-infra-setup/SKILL.md) conventions for Azure targets.

Sanitize internal-only details — the external variant must **not** leak Forward Path internal state or secrets:

| Remove / externalize | Keep / parameterize |
|----------------------|---------------------|
| Internal backend/state config, Forward Path subscription IDs, internal RBAC principals | Customer-supplied subscription/tenant, resource group, region |
| Hardcoded secret values, connection strings | Secret **names** + Key Vault references the customer populates |
| Forward Path-only CI/OIDC federation subjects | Image references + instructions to pull from the shared/registry the customer is granted |
| Internal hostnames, internal-only resources | Customer-facing inputs as documented variables with descriptions |

Document every required input variable with a clear description so the customer knows what to supply.

Complete this step when the handoff folder contains customer-runnable Terraform and Bicep (or the user-scoped subset), no internal-only state/secrets/principals remain, and every required customer input is parameterized and documented.

### Step 4: Fill the deployment instructions from the Notion template

Retrieve the sample template page (`36c92ad1579b81819801cfd3276fe396`) and use its exact section structure. Fill in everything the customer needs to stand the app up themselves, including:

- **Prerequisites** — required cloud account, CLI tools, permissions/roles.
- **App registrations / identities** — what to create, required API permissions, redirect URIs, OIDC/federated credentials.
- **Environment variables** — every env var the services need, with description and whether it is a secret.
- **Secrets** — names to create (e.g. in Key Vault), which values come from the **1Password share link** for ACR image pull credentials, and which values the customer must supply from their own third-party accounts (for example OpenRouter API keys).
- **Images / services** — each service image, where to pull it from, and tags.
- **Deploy steps** — how to run the included Terraform/Bicep, in order.
- **Verification** — how to confirm a healthy deployment.

Treat the sample template page as **read-only**: copy its structure and draft the filled content for the new database page in Step 5, but never edit the sample template in place. Do not paste secret values into the page. Reference the 1Password link only for ACR image pull credentials, and describe third-party service secrets as customer-supplied values.

Complete this step when the filled instructions preserve the template structure and cover prerequisites, identities, env vars, secrets, images, deployment steps, and verification with no secret values pasted.

### Step 5: Save the filled page into the Notion deployments database

Create a new page in the target database (`49466b35ef21421199f5acb7be5bf9e0`) with the filled content. Title it following the template pattern, substituting real values:

```
Deployment Instructions - <App> - <Customer>
```

Set any database properties (customer, app, date/version) that the database defines. Record the new page URL.

Complete this step when the new page exists in the target database, relevant properties are set, and the page URL is recorded.

### Step 6: Export the Notion page and assemble the customer folder

Use Notion's built-in **Export** on the saved page (Markdown & CSV, or PDF per customer preference) to get the customer-facing document. If export is not available through the connected tools, ask the user to export the saved page manually, or retrieve the saved page content and assemble an equivalent `README.md` that preserves the template structure. Then assemble the package folder under `docs/deployments/` using the same Windows-safe sanitized `<Customer>` and `<App>` values required for the zip filename in Step 7:

```
docs/deployments/
└── <Sanitized-Customer>-<Sanitized-App>-Deployment-<YYYY-MM-DD>/
    ├── README.(md|pdf)        # exported deployment instructions
    ├── infra/
    │   ├── terraform/         # external Terraform
    │   └── bicep/             # external Bicep
    └── (any supporting assets from the export, e.g. images/)
```

The exported instructions are the entry point — make sure they reference the `infra/` contents, the 1Password link for ACR image pull credentials, and the customer-supplied third-party secrets they must configure. Before zipping, verify the handoff folder is visible to git with `git status --short docs/deployments/<Sanitized-Customer>-<Sanitized-App>-Deployment-<YYYY-MM-DD>/`; if it is ignored, move it to a tracked location or ask before changing ignore rules.

Complete this step when the package folder contains the exported instructions or equivalent `README.md`, the external infra, any supporting assets, and a git visibility check has passed.

### Step 7: Zip with a Windows-safe name and deliver

Zip the checked-in handoff folder. The filename **must** be valid on Windows. The zip can be a generated delivery artifact, but the source deployment instructions and infra folder must remain in a git-tracked path.

Naming convention:

```
<Customer>-<App>-Deployment-<YYYY-MM-DD>.zip
```

Sanitize `<Customer>` and `<App>` to alphanumerics and hyphens (replace spaces and other separators with `-`). See [Windows-safe naming](#windows-safe-naming) below.

```bash
zip -r "Acme-Insurance-PolicyBot-Deployment-2026-06-05.zip" "docs/deployments/Acme-Insurance-PolicyBot-Deployment-2026-06-05/"
```

Deliver the zip and report: the zip path/filename, the Notion page URL, a reminder that only the ACR image pull username/password are in the linked 1Password share, and that third-party service secrets are customer-supplied.

Complete this step when the zip filename is Windows-safe, the archive contains the handoff folder, and the final report includes the zip path, Notion page URL, ACR credential reminder, and customer-supplied third-party secret reminder.

## Windows-safe naming

Windows forbids these characters in filenames — never use them (pipes `|` especially come up):

```
< > : " / \ | ? *
```

Also avoid:
- Control characters (0x00–0x1F).
- Trailing spaces or trailing dots (`Name .zip`, `Name..zip`).
- Reserved device names as the base name: `CON`, `PRN`, `AUX`, `NUL`, `COM1`–`COM9`, `LPT1`–`LPT9`.

Prefer `-` as the separator. Keep dates as `YYYY-MM-DD` (no `/`).

## Anti-patterns

- Shipping the **internal** infra verbatim (leaking state config, internal subscription IDs, RBAC principals, or secret values).
- Putting secret **values** in the zip or in Notion instead of documenting where they come from.
- Telling the customer that third-party service secrets (for example OpenRouter API keys) are in 1Password; 1Password is only for Forward Path-provided ACR image pull credentials.
- Inventing a new instructions structure instead of copying the Notion template page.
- Generating Azure infra without confirming the customer's actual target cloud.
- Filenames containing `|`, `:`, `/`, or other Windows-forbidden characters.
- Saving the page outside the target deployments database, or skipping the Notion record entirely.
- Creating the source deployment instructions or external infra under `dist/`, `build/`, or another ignored/generated-output directory when the handoff must be checked into git.

## Additional resources

- Forward Path Azure conventions: [azure-infra-setup/SKILL.md](../azure-infra-setup/SKILL.md)
- Notion sample template page: `36c92ad1579b81819801cfd3276fe396`
- Notion deployments database: `49466b35ef21421199f5acb7be5bf9e0`
