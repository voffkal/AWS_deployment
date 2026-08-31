# ML API on AWS ECS — differential testing and containerised deployment

A house-price regression model served over a Flask API, packaged into a Docker
image, pushed to Amazon ECR and rolled out on ECS Fargate from CI.

Built while working through a deployment course. The interesting part is not
the model — it is deliberately simple — but everything around it: how a model
is versioned, how a retrained one is prevented from silently regressing, and
how the whole thing reaches a running service.

## Differential testing

Unit tests pin behaviour to fixed expectations. That works for code, but not
for a retrained model: assertions either break on every change, or are so
loose that a genuinely broken model still passes. Differential testing answers
a different question — *did this model start predicting something else?*

```
CI: capture predictions from the deployed model ──> test_data_predictions.csv
                                                             │
CI: train the candidate model                                │
                                                             ↓
    predict on the same rows ───────────────>  compare, row by row
                                               fail if |Δ| > 5%
```

- `tests/capture_model_predictions.py` records the current model's output.
  It runs **only in CI** — running it locally would overwrite the baseline
  with predictions from whatever model happens to be installed.
- `tests/differential_tests/test_differential.py` re-predicts and compares
  against that baseline within `ACCEPTABLE_MODEL_DIFFERENCE` (5%).
- The job runs *before* the model is published, so a divergent model never
  reaches the package index — and therefore never reaches an image.

The 5% tolerance is a judgement call: tight enough to catch a broken
preprocessing step, loose enough to tolerate library-level float differences.

## Pipeline

```
push ──> test model ──> test API ──> differential tests
                                            │
                              publish model as a GitHub Release
                                            │
                                  (main only) build image
                                            ↓
                              ECR ──> ecs update-service --force-new-deployment
```

Each stage gates the next: a model that fails its own tests is never packaged,
and an image is only built from a commit whose model was published.

This pipeline has actually been run end to end on AWS — the image was built,
pushed to ECR, deployed on Fargate, and served real predictions before being
torn down. See [docs/deployment-run.md](docs/deployment-run.md) for the live
responses and the teardown commands.

## Layout

```
packages/
  regression_model/   Lasso model, installable package, owns its own tests
  ml_api/             Flask API + marshmallow request validation
Dockerfile            builds the API image
Makefile              build / tag / push targets for ECR
.circleci/config.yml  the pipeline above
```

The model package is the unit of deployment: the API depends on it as an
ordinary versioned artifact rather than importing source from a sibling
directory, so an image records exactly which trained model it ships.

The course published that package to a private Gemfury index. This repo uses
**GitHub Releases** instead - free, and it works the same way: `publish_model.sh`
builds the wheel and attaches it to a `model-v<version>` release, and every job
that needs the model pulls that release with `gh release download`. The script
refuses to publish a wheel with no trained pipeline inside it, which is the one
failure this setup can hide.

## Request validation

The API refuses a batch outright when a row is missing a feature the model
actually needs, instead of predicting on what is left and returning fewer
results than rows submitted:

```
POST /v1/predict/regression
  row missing MSZoning / KitchenQual / BsmtFullBath / GarageCars
  -> 400, naming the offending rows
```

Nulls elsewhere are accepted. In the Ames dataset a missing value is often
*the* value — `NA` in `GarageCond` means "no garage", not "data lost" — and
none of those fields is a model feature, so a null there cannot change a
prediction. Rejecting them would refuse the shipped Kaggle test set over
data that is perfectly valid.

## Configuration

Nothing secret is committed. The build reads from the environment:

| Variable | Purpose |
|---|---|
| `GH_TOKEN` | publishing and downloading the model release |
| `AWS_ACCOUNT_ID` | ECR registry account |
| `AWS_REGION` | ECR/ECS region (defaults to `ap-northeast-2`) |
| `SECRET_KEY` | Flask secret |

The `Makefile` targets fail fast if a required variable is missing rather than
building a broken image.

## Running it

Build for the right architecture: Fargate runs X86_64, so an image built on an
ARM Mac without `--platform linux/amd64` dies with `exec format error`.

```bash
# locally
pip install -r packages/ml_api/requirements.txt
PYTHONPATH=./packages/ml_api python packages/ml_api/run.py

# tests (differential ones need a CI-captured baseline)
cd packages/ml_api && tox

# container (fetches the model release first)
make build-ml-api-aws
docker run -p 5000:5000 vve-ml-api:$(git rev-parse HEAD)

# ship it
make tag-ml-api push-ml-api-aws
```

Endpoints: `GET /health`, `GET /version`, `POST /v1/predict/regression`.

## Known limitations

Kept deliberately — this is coursework, not a production service:

- Deployment is a forced service update, not blue/green or canary: a bad image
  goes straight to all tasks.
- No smoke test after `ecs update-service` — CI reports success once the API
  call returns, not once the new tasks are healthy.
- The differential baseline is a single CSV regenerated by CI each run, not a
  versioned artifact store.
