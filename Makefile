NAME=vve-ml-api
AWS_REGION ?= ap-northeast-2
COMMIT_ID=$(shell git rev-parse HEAD)

# The model package comes from its GitHub Release, not a private index, so the
# only credential the build needs is whatever `gh` is already authenticated with.
fetch-model:
	@command -v gh >/dev/null || (echo "gh CLI is required" && exit 1)
	@rm -rf model_pkg
	@TAG=$$(gh release list --json tagName -q '[.[].tagName | select(startswith("model-v"))][0]'); \
	  test -n "$$TAG" || (echo "no model-v* release published yet" && exit 1); \
	  echo "Using model release $$TAG"; \
	  gh release download "$$TAG" -D model_pkg -p '*.whl' --clobber

build-ml-api-aws: fetch-model
	docker build -t $(NAME):$(COMMIT_ID) .

tag-ml-api:
	@test -n "$(AWS_ACCOUNT_ID)" || (echo "AWS_ACCOUNT_ID is not set" && exit 1)
	docker tag $(NAME):$(COMMIT_ID) $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/$(NAME):latest

push-ml-api-aws:
	@test -n "$(AWS_ACCOUNT_ID)" || (echo "AWS_ACCOUNT_ID is not set" && exit 1)
	docker push $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/$(NAME):latest
