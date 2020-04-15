KIWI_VERSION=8.2-mt

.PHONY: docker-image
docker-image:
	docker build -t docker.io/mrsenko/kiwitcms-enterprise:$(KIWI_VERSION) .
	docker tag docker.io/mrsenko/kiwitcms-enterprise:$(KIWI_VERSION) docker.io/mrsenko/kiwitcms-enterprise:latest

.PHONY: flake8
flake8:
	@flake8 --exclude=.git *.py tcms_enterprise tcms_settings_dir
