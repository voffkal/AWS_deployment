# Deploying an ML API to AWS ECS

The house-price Flask API from the earlier stages, taken the last step: built
as a Docker image, pushed to Amazon ECR, and rolled out on ECS Fargate through
CI.

## Pipeline

```
push ──> test model ──> test API ──> differential tests
                                            │
                                    publish model to index
                                            │
                                  (main only) build image
                                            ↓
                              ECR ──> ecs update-service --force-new-deployment
```

Each stage gates the next: a model that fails its own tests is never packaged,
and an image is only built from a commit whose model was published.

## Layout

```
packages/
  regression_model/   Lasso model, installable package
  ml_api/             Flask API, gunicorn entrypoint
Dockerfile            builds the API image, installs the model from the index
Makefile              build / tag / push targets for ECR
.circleci/config.yml  the pipeline above
```

## Configuration

Nothing secret is committed. The build reads from the environment:

| Variable | Purpose |
|---|---|
| `PIP_EXTRA_INDEX_URL` | credentials for the private package index |
| `AWS_ACCOUNT_ID` | ECR registry account |
| `AWS_REGION` | ECR/ECS region (defaults to `ap-northeast-2`) |
| `SECRET_KEY` | Flask secret |

The `Makefile` targets fail fast if a required variable is missing rather than
building a broken image.

## Running it

```bash
# locally
pip install -r packages/ml_api/requirements.txt
PYTHONPATH=./packages/ml_api python packages/ml_api/run.py

# container
make build-ml-api-aws
docker run -p 5000:5000 vve-ml-api:$(git rev-parse HEAD)

# ship it
make tag-ml-api push-ml-api-aws
```

Endpoints: `GET /health`, `GET /version`, `POST /v1/predict/regression`.

## Known limitations

- **Validation errors do not block a prediction.** The endpoint answers `200`
  even when rows fail validation, returning fewer predictions than rows sent.
  See the `TODO` in `api/controller.py`.
- Deployment is a forced service update, not a blue/green or canary rollout —
  a bad image goes straight to all tasks.
- No smoke test after `ecs update-service`; CI reports success once the API
  call returns, not once the new tasks are healthy.
