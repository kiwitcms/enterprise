KIWI_VERSION=6.10-mt

docker-image:
	docker build -t docker.io/mrsenko/kiwitcms-enterprise:$(KIWI_VERSION) .
	docker tag docker.io/mrsenko/kiwitcms-enterprise:$(KIWI_VERSION) docker.io/mrsenko/kiwitcms-enterprise:latest
