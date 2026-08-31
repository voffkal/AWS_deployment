NAME=vve-ml-api
AWS_REGION ?= ap-northeast-2
COMMIT_ID=$(shell git rev-parse HEAD)

# PIP_EXTRA_INDEX_URL holds the private package index credentials and must be
# supplied by the environment (CI secret / local shell), never committed here.
build-ml-api-aws:
	@test -n "$(PIP_EXTRA_INDEX_URL)" || (echo "PIP_EXTRA_INDEX_URL is not set" && exit 1)
	docker build --build-arg PIP_EXTRA_INDEX_URL=$(PIP_EXTRA_INDEX_URL) -t $(NAME):$(COMMIT_ID) .

tag-ml-api:
	@test -n "$(AWS_ACCOUNT_ID)" || (echo "AWS_ACCOUNT_ID is not set" && exit 1)
	docker tag $(NAME):$(COMMIT_ID) $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/$(NAME):latest

push-ml-api-aws:
	@test -n "$(AWS_ACCOUNT_ID)" || (echo "AWS_ACCOUNT_ID is not set" && exit 1)
	docker push $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/$(NAME):latest
