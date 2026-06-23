# CI/CD Setup Walkthrough

Deploy this ETL Lambda pipeline with **GitHub Actions (CI)** + **AWS CodePipeline (CD)**.

**Time:** ~30 min | **Pick one AWS region** (e.g. `eu-north-1`) and stay in it for all steps.

---

## Prerequisites

- GitHub account + [new repo](https://github.com/new) (fork or push this code)
- AWS account with console access
- Lambda, S3 bucket, and DynamoDB table for ETL (or create during setup)

**Values to note before starting** (replace with yours):

| Variable | Example | Used in |
|----------|---------|---------|
| GitHub user/repo | `your-user/data-pipeline-cicd-demo` | CodePipeline Source |
| Lambda name | `etl-customer-s3-to-dynamodb` | Deploy stage |
| S3 source bucket | `testingrawdata` | Lambda runtime |
| DynamoDB table | `etl-test` | Lambda runtime |
| Artifact bucket | `cicd-artifacts-<account-id>-<region>` | CodePipeline artifacts |

---

## 1. Push code to GitHub

```bash
git clone https://github.com/YOUR_GITHUB_USER/data-pipeline-cicd-demo.git
cd data-pipeline-cicd-demo
```

**Verify locally (optional):**

```bash
pip install -r requirements-dev.txt
flake8 lambda tests --max-line-length=100
pytest tests/ -v
```

Push to `main` → open repo **Actions** tab → confirm **CI - Data Pipeline** workflow is green.

---

## 2. Application code map

| File | Purpose |
|------|---------|
| `lambda/etl_customer/transform.py` | Pure ETL logic — unit tested |
| `lambda/etl_customer/lambda_function.py` | Lambda handler — S3 → DynamoDB |
| `tests/test_transform.py` | Unit tests |
| `buildspec.yml` | CodeBuild: lint → test → zip |
| `.github/workflows/ci-data-pipeline.yml` | GitHub Actions CI on push/PR |

---

## 3. Lambda (Console)

**Console:** [Lambda → Functions](https://console.aws.amazon.com/lambda/home)

1. **Create function** (or use existing)
   - Runtime: **Python 3.12**
   - Handler: `lambda_function.lambda_handler`
2. **Configuration → Environment variables**
   - `S3_BUCKET`, `S3_KEY`, `DYNAMODB_TABLE` (match your data sources)
3. **Configuration → Permissions**
   - Attach a role with S3 read + DynamoDB write (see `infra/lambda-permissions-policy.json`)
4. **Actions → Publish new version** (creates version `1`)
5. **Aliases → Create alias**
   - Name: `prod` → Version: `1`

> CodePipeline Deploy stage in `infra/codepipeline.json` targets this function + alias.

---

## 4. AWS CD infrastructure (Console)

Use `infra/*.json` as reference while creating resources in the console.

### 4a. S3 artifact bucket

**Console:** [S3 → Create bucket](https://s3.console.aws.amazon.com/s3/create)

- Name: `cicd-artifacts-<your-account-id>-<region>`
- Matches `artifactStore.location` in `infra/codepipeline.json`

### 4b. GitHub connection

**Console:** [Developer Tools → Connections](https://console.aws.amazon.com/codesuite/settings/connections)

1. **Create connection** → Provider: **GitHub** → Name: `github-cicd-demo`
2. **Update pending connection** → authorize GitHub → status **Available**
3. Copy the **Connection ARN** → paste into `infra/codepipeline-policy.json` and `infra/codepipeline.json` (`__CONNECTION_ARN__`) before creating the pipeline role

### 4c. IAM roles

**Console:** [IAM → Roles → Create role](https://console.aws.amazon.com/iam/home#/roles)

| Role name | Trusted entity | Policy source |
|-----------|----------------|---------------|
| `data-pipeline-codebuild-role` | CodeBuild | `infra/codebuild-trust-policy.json` + `infra/codebuild-policy.json` |
| `data-pipeline-codepipeline-role` | CodePipeline | `infra/codepipeline-trust-policy.json` + `infra/codepipeline-policy.json` |

Replace `__ARTIFACT_BUCKET__`, `__AWS_REGION__`, `__AWS_ACCOUNT_ID__`, `__LAMBDA_NAME__`, and `__CONNECTION_ARN__` in the policy JSON before attaching.

### 4d. CodeBuild project

**Console:** [CodeBuild → Create project](https://console.aws.amazon.com/codesuite/codebuild/projects/create)

| Setting | Value |
|---------|-------|
| Name | `etl-customer-build` (see `infra/codebuild-project.json`) |
| Source | **CodePipeline** |
| Environment | Managed image, Ubuntu, Standard, Python support |
| Buildspec | **Use buildspec file** → `buildspec.yml` |
| Artifacts | **CodePipeline** |
| Service role | `data-pipeline-codebuild-role` |

### 4e. CodePipeline (V2)

**Console:** [CodePipeline → Create pipeline](https://console.aws.amazon.com/codesuite/codepipeline/pipelines/create)

- Pipeline type: **V2**
- Service role: `data-pipeline-codepipeline-role`
- Artifact store: your S3 artifact bucket

| Stage | Provider | Config (see `infra/codepipeline.json`) |
|-------|----------|----------------------------------------|
| **Source** | GitHub (CodeStar Connection) | Connection, repo `your-user/data-pipeline-cicd-demo`, branch `main` |
| **Build** | CodeBuild | Project `etl-customer-build` |
| **Deploy** | AWS Lambda | Function name, Alias `prod`, Strategy **All at once** |

**Release change** or push to `main` to start the first run.

---

## 5. Flow on `git push main`

```
Push to main
  ├─ GitHub Actions (.github/workflows/ci-data-pipeline.yml) → flake8 + pytest
  └─ CodePipeline (infra/codepipeline.json)
       ├─ Source  → pull repo via CodeStar connection
       ├─ Build   → buildspec.yml → function.zip
       └─ Deploy  → Lambda alias prod
```

---

## 6. Verify (Console)

### CodePipeline

**Console:** [CodePipeline → `data-pipeline-etl-cd`](https://console.aws.amazon.com/codesuite/codepipeline/pipelines)

- All three stages show **Succeeded** (green)
- Click **Build** stage → **Details** → open CodeBuild logs (flake8, pytest, zip)
- Click **Deploy** stage → confirm “Updated function code and published new version”

### Lambda deployed

**Console:** [Lambda → your function → Versions](https://console.aws.amazon.com/lambda/home)

- **Last modified** timestamp updated after pipeline run
- **Aliases** tab → `prod` points to a new version number

### Test invoke

**Console:** Lambda → **Test** tab (or **Test** button)

- Create test event, e.g.:
  ```json
  {"bucket": "testingrawdata", "key": "data-etl-test1/customer.csv"}
  ```
- **Test** → check response shows `"message": "ETL completed successfully"`

### DynamoDB output

**Console:** [DynamoDB → Tables → `etl-test` → Explore items](https://console.aws.amazon.com/dynamodbv2/home)

- Confirm customer records loaded after invoke

### GitHub CI

**GitHub:** repo → **Actions** → latest **CI - Data Pipeline** run → green check

---

## Customize

| Change | Edit |
|--------|------|
| Lint/test rules | `buildspec.yml` + `.github/workflows/ci-data-pipeline.yml` |
| Deploy target | `infra/codepipeline.json` → Deploy `FunctionName` / `FunctionAlias` |
| Trigger branch | `infra/codepipeline.json` → Source `BranchName` |
| Manual approval | CodePipeline → Edit → Add **Approval** stage between Build and Deploy |

---

## Cleanup (Console)

| Resource | Console path |
|----------|--------------|
| Pipeline | CodePipeline → `data-pipeline-etl-cd` → Delete |
| CodeBuild | CodeBuild → `etl-customer-build` → Delete |
| Artifact bucket | S3 → empty bucket → Delete |
| IAM roles | IAM → Roles → delete `data-pipeline-codepipeline-role`, `data-pipeline-codebuild-role` |
| Connection | Developer Tools → Connections → delete `github-cicd-demo` |

---

## Optional: CLI scripts

For automated provisioning, see `scripts/setup-aws.sh` and `scripts/render-infra.sh` (not required if using the console steps above).
