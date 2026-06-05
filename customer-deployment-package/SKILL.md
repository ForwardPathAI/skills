---
name: customer-deployment-package
description: Produce a customer-facing deployment handoff package for a Forward Path custom app — an external Terraform/Bicep variant of the repo's internal infra, customer setup instructions (env vars, app registrations, secrets via 1Password), filled into the Notion deployment-instructions template, saved to the Notion deployments database, then exported and zipped with a Windows-safe filename. Use when the user asks to create a customer deployment package, external infra, deployment handoff, customer install/setup instructions, or to export/zip deployment instructions for a client.
---

# Customer Deployment Package

Forward Path builds custom AI software and hands customers a self-contained package to deploy it in **their own** cloud tenant. This skill turns a repo's **internal** infrastructure into an **external** customer deliverable: sanitized Terraform/Bicep, written setup instructions, and a 1Password link for credentials — captured in Notion, then exported and zipped for the customer.

Customers are usually **Azure** customers and usually on **Windows**, so the final artifact must use a Windows-safe filename.

## Prerequisites

- Run from the **application repo** (the one with the internal `infra/` or `infrastructure/` folder).
- **Notion MCP** connected. Inspect available tools/params under the MCP descriptors before calling (search, retrieve page, create page in a database, etc.). Stop and tell the user if no Notion MCP is available.
- **1Password** share link for the customer's image/registry credentials and any handoff secrets (created by a human — do not put secret values in the zip or in git).
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
- The **1Password share link** for credentials/secrets.
- App version, if using versioned naming.

### Step 2: Locate internal infra

Find the internal infra (commonly `infra/`, `infrastructure/`, `terraform/`, or `bicep/`). Read it to understand resources, env vars, app registrations, secret names, and image references. This internal infra is the source of truth; the external variant is a **derivative**, not a copy.

### Step 3: Build the external infra variant

Create an external infra set the **customer** can run in their tenant. Keep it in a working folder (e.g. `dist/customer-package/infra/`), not mixed into the repo's internal infra.

Include **both Terraform and Bicep** (unless the user scopes to one). Apply [azure-infra-setup](../azure-infra-setup/SKILL.md) conventions for Azure targets.

Sanitize internal-only details — the external variant must **not** leak Forward Path internal state or secrets:

| Remove / externalize | Keep / parameterize |
|----------------------|---------------------|
| Internal backend/state config, Forward Path subscription IDs, internal RBAC principals | Customer-supplied subscription/tenant, resource group, region |
| Hardcoded secret values, connection strings | Secret **names** + Key Vault references the customer populates |
| Forward Path-only CI/OIDC federation subjects | Image references + instructions to pull from the shared/registry the customer is granted |
| Internal hostnames, internal-only resources | Customer-facing inputs as documented variables with descriptions |

Document every required input variable with a clear description so the customer knows what to supply.

### Step 4: Fill the deployment instructions from the Notion template

Retrieve the sample template page (`36c92ad1579b81819801cfd3276fe396`) and use its exact section structure. Fill in everything the customer needs to stand the app up themselves, including:

- **Prerequisites** — required cloud account, CLI tools, permissions/roles.
- **App registrations / identities** — what to create, required API permissions, redirect URIs, OIDC/federated credentials.
- **Environment variables** — every env var the services need, with description and whether it is a secret.
- **Secrets** — names to create (e.g. in Key Vault), and a pointer to the **1Password share link** for the values Forward Path provides.
- **Images / services** — each service image, where to pull it from, and tags.
- **Deploy steps** — how to run the included Terraform/Bicep, in order.
- **Verification** — how to confirm a healthy deployment.

Do not paste secret values into the page — reference the 1Password link instead.

### Step 5: Save the filled page into the Notion deployments database

Create a new page in the target database (`49466b35ef21421199f5acb7be5bf9e0`) with the filled content. Title it following the template pattern, substituting real values:

```
Deployment Instructions - <App> - <Customer>
```

Set any database properties (customer, app, date/version) that the database defines. Record the new page URL.

### Step 6: Export the Notion page and assemble the customer folder

Use Notion's built-in **Export** on the saved page (Markdown & CSV, or PDF per customer preference) to get the customer-facing document. If export is not available through the connected tools, ask the user to export the saved page manually, or retrieve the saved page content and assemble an equivalent `README.md` that preserves the template structure. Then assemble the package folder:

```
<Customer>-<App>-Deployment-<YYYY-MM-DD>/
├── README.(md|pdf)            # exported deployment instructions
├── infra/
│   ├── terraform/             # external Terraform
│   └── bicep/                 # external Bicep
└── (any supporting assets from the export, e.g. images/)
```

The exported instructions are the entry point — make sure they reference the `infra/` contents and the 1Password link.

### Step 7: Zip with a Windows-safe name and deliver

Zip the assembled folder. The filename **must** be valid on Windows.

Naming convention:

```
<Customer>-<App>-Deployment-<YYYY-MM-DD>.zip
```

Sanitize `<Customer>` and `<App>` to alphanumerics and hyphens (replace spaces and other separators with `-`). See [Windows-safe naming](#windows-safe-naming) below.

```bash
zip -r "Acme-Insurance-PolicyBot-Deployment-2026-06-05.zip" "Acme-Insurance-PolicyBot-Deployment-2026-06-05/"
```

Deliver the zip and report: the zip path/filename, the Notion page URL, and a reminder that credentials are in the linked 1Password share.

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
- Putting secret **values** in the zip or in Notion instead of the 1Password share link.
- Inventing a new instructions structure instead of copying the Notion template page.
- Generating Azure infra without confirming the customer's actual target cloud.
- Filenames containing `|`, `:`, `/`, or other Windows-forbidden characters.
- Saving the page outside the target deployments database, or skipping the Notion record entirely.

## Additional resources

- Forward Path Azure conventions: [azure-infra-setup/SKILL.md](../azure-infra-setup/SKILL.md)
- Notion sample template page: `36c92ad1579b81819801cfd3276fe396`
- Notion deployments database: `49466b35ef21421199f5acb7be5bf9e0`
