# Data Pipeline CI/CD Demo

ETL Lambda (S3 → DynamoDB) with GitHub Actions CI and AWS CodePipeline CD.

**Setup guide:** follow the 7 steps in **[SETUP-WALKTHROUGH.md](SETUP-WALKTHROUGH.md)**

1. Create a new repo  
2. Clone this shared code  
3. Copy folders into your repo locally  
4. Push to GitHub  
5. Verify GitHub Actions  
6. Integrate AWS CodePipeline  
7. Verify CodePipeline  

## Repo structure

```
.github/workflows/ci-data-pipeline.yml   # CI: lint + pytest
buildspec.yml                            # CD: CodeBuild steps
lambda/etl_customer/                     # Lambda source
tests/                                   # Unit tests
infra/                                   # IAM + CodePipeline templates
scripts/                                 # Optional CLI setup
```

## Architecture

```
git push main → GitHub Actions (CI) + CodePipeline (CD)
CodePipeline: Source → CodeBuild → Lambda Deploy (alias prod)
```
