ifeq ($(DOCKER_ORG),)
  DOCKER_ORG=mrsenko
endif

ifeq ($(KIWI_VERSION),)
    KIWI_VERSION=3.49-ee
endif

docker-image:
	docker build -t $(DOCKER_ORG)/kiwi:$(KIWI_VERSION) .
	docker tag $(DOCKER_ORG)/kiwi:$(KIWI_VERSION) $(DOCKER_ORG)/kiwi:latest
