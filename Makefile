ifeq ($(DOCKER_ORG),)
  DOCKER_ORG=mrsenko
endif

ifeq ($(KIWI_VERSION),)
    KIWI_VERSION=4.1.0-ee
endif

docker-image:
	docker build -t $(DOCKER_ORG)/kiwi:$(KIWI_VERSION) .
	docker tag $(DOCKER_ORG)/kiwi:$(KIWI_VERSION) $(DOCKER_ORG)/kiwi:latest
