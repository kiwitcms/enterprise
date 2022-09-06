KIWI_VERSION=$(shell python3 setup.py --version)
ENTERPRISE_VERSION=$(KIWI_VERSION)-mt

.PHONY: echo-version
echo-version:
	@echo $(ENTERPRISE_VERSION)


.PHONY: build
build:
	sudo rm -rf dist/ build/ *.egg-info/
	python3 setup.py sdist
	python3 setup.py bdist_wheel
	twine check dist/*


.PHONY: build-gssapi
build-gssapi:
	docker pull registry.access.redhat.com/ubi8/ubi-minimal
	docker build -t kiwitcms/gssapi-buildroot -f Dockerfile.gssapi .
	docker run --rm --security-opt label=disable \
	    -v `pwd`/dist/:/host kiwitcms/gssapi-buildroot /bin/bash -c 'cp /dist/*.whl /host/'
	docker rmi kiwitcms/gssapi-buildroot

.PHONY: build-xmlsec
build-xmlsec:
	docker pull quay.io/centos/centos:stream8
	docker build -t kiwitcms/xmlsec-buildroot -f Dockerfile.xmlsec .
	docker run --rm --security-opt label=disable \
	    -v `pwd`/dist/:/host kiwitcms/xmlsec-buildroot /bin/bash -c 'cp /dist/*.whl /host/'
	docker rmi kiwitcms/xmlsec-buildroot


.PHONY: docker-image
docker-image: build build-gssapi build-xmlsec
	# everything else below is Enterprise + multi-tenant
	docker build --build-arg KIWI_VERSION=$(KIWI_VERSION) -t quay.io/kiwitcms/enterprise:$(ENTERPRISE_VERSION) .
	docker tag quay.io/kiwitcms/enterprise:$(ENTERPRISE_VERSION) quay.io/kiwitcms/enterprise:latest


.PHONY: docker-manifest
docker-manifest:
	# versioned manifest
	docker manifest rm quay.io/kiwitcms/enterprise:$(ENTERPRISE_VERSION) \
	docker manifest create \
	    quay.io/kiwitcms/enterprise:$(ENTERPRISE_VERSION) \
	    quay.io/kiwitcms/enterprise:$(ENTERPRISE_VERSION)-x86_64 \
	    quay.io/kiwitcms/enterprise:$(ENTERPRISE_VERSION)-aarch64
	docker manifest push quay.io/kiwitcms/enterprise:$(ENTERPRISE_VERSION)

	# latest manifest
	docker manifest rm quay.io/kiwitcms/enterprise:latest \
	docker manifest create \
	    quay.io/kiwitcms/enterprise:latest \
	    quay.io/kiwitcms/enterprise:$(ENTERPRISE_VERSION)-x86_64 \
	    quay.io/kiwitcms/enterprise:$(ENTERPRISE_VERSION)-aarch64
	docker manifest push quay.io/kiwitcms/enterprise:latest


.PHONY: flake8
flake8:
	@flake8 --exclude=.git *.py tcms_enterprise tcms_settings_dir

KIWI_LINT_INCLUDE_PATH="../Kiwi"

.PHONY: pylint
pylint:
	if [ ! -d "$(KIWI_LINT_INCLUDE_PATH)/kiwi_lint" ]; then \
	    git clone --depth 1 https://github.com/kiwitcms/Kiwi.git $(KIWI_LINT_INCLUDE_PATH); \
	fi

	PYTHONPATH=$(KIWI_LINT_INCLUDE_PATH):. \
	DJANGO_SETTINGS_MODULE=l10n_settings \
	pylint --load-plugins=pylint_django --load-plugins=kiwi_lint \
	    -d missing-docstring -d duplicate-code -d module-in-directory-without-init -d similar-string \
	    *.py tcms_enterprise/ tcms_settings_dir/

.PHONY: messages
messages:
	./manage.py makemessages --settings l10n_settings --locale en --no-obsolete --ignore "test*.py"
	ls tcms_enterprise/locale/*/LC_MESSAGES/*.po | xargs -n 1 -I @ msgattrib -o @ --no-fuzzy @
