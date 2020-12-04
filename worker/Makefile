REPO=swarnalathanatarajan
IMAGE1=worker
TAG=v1

buildrest:
docker build -t $(IMAGE1):$(TAG) --file Dockerfile-worker .
docker tag $(IMAGE1):$(TAG) $(REPO)/$(IMAGE1):$(TAG)
docker push $(REPO)/$(IMAGE1):$(TAG)
