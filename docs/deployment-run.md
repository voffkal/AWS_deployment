# Deployment run — 2026-08-31

A record of this pipeline actually running end to end on AWS. The service was
torn down immediately afterwards: ECS Fargate is not in the AWS free tier and
bills per second, so leaving a demo running costs money for nothing.

## What was deployed

| | |
|---|---|
| Image | `184471688556.dkr.ecr.ap-northeast-2.amazonaws.com/vve-ml-api:latest` |
| Digest | `sha256:1097c1eed527f298d6b38a7b74d8eb3da1bc24fecddb95fadb9637c5804d6664` |
| Model package | vve-regression-model 0.0.4 (wheel with the trained pipeline inside) |
| Platform | Fargate, X86_64, 256 CPU / 512 MB |
| Region | ap-northeast-2 |

The image is built `--platform linux/amd64`: this Mac is ARM64, and an ARM
image fails on Fargate's X86_64 runtime with `exec format error`.

## Live responses

```
GET /health
ok

GET /version
{"api_version":"0.4","model_version":"0.0.4"}

POST /v1/predict/regression        # three valid rows
200  {"predictions": [112511, 142036, 174727], "errors": null}

POST /v1/predict/regression        # one row with a null KitchenQual
400  {"errors": {"1": {"KitchenQual": ["Field may not be null."]}}}
```

The last one is the point of the validation work: `KitchenQual` is a feature
the pipeline has no imputer for, so the batch is refused instead of quietly
returning fewer predictions than rows submitted.

## Task startup

```
PROVISIONING -> PENDING -> RUNNING   (~70s)
```

## Teardown

```bash
aws ecs update-service --cluster vve-ml-api-cluster \
  --service vve-ml-api-task-service --desired-count 0
aws ecs delete-service --cluster vve-ml-api-cluster \
  --service vve-ml-api-task-service --force
aws ecs delete-cluster --cluster vve-ml-api-cluster
```

The ECR repository and the image are kept: 500 MB of private storage is inside
the free tier, and the image is what a redeploy would start from.
