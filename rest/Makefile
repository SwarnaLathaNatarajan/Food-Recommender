REPO=swarnalathanatarajan
IMAGE1=rest
IMAGE2=logs
TAG=v1

buildrest:
docker build -t $(IMAGE1):$(TAG) --file Dockerfile-rest .
docker tag $(IMAGE1):$(TAG) $(REPO)/$(IMAGE1):$(TAG)
docker push $(REPO)/$(IMAGE1):$(TAG)

buildlogs:
docker build -t $(IMAGE2):$(TAG) --file Dockerfile-logs .
docker tag $(IMAGE2):$(TAG) $(REPO)/$(IMAGE2):$(TAG)
docker push $(REPO)/$(IMAGE2):$(TAG