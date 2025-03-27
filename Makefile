# Copyright (c) 2017-2025 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

KIWI_VERSION=$(shell python3 setup.py --version)
ENTERPRISE_VERSION=$(KIWI_VERSION).6-mt

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
	docker pull registry.access.redhat.com/ubi9-minimal
	docker build -t kiwitcms/gssapi-buildroot -f Dockerfile.gssapi .
	docker run --rm --security-opt label=disable \
	    -v `pwd`/dist/:/host kiwitcms/gssapi-buildroot /bin/bash -c 'cp /dist/*.whl /host/'
	docker rmi kiwitcms/gssapi-buildroot

.PHONY: build-xmlsec
build-xmlsec:
	docker pull quay.io/centos/centos:stream9
	docker build -t kiwitcms/xmlsec-buildroot -f Dockerfile.xmlsec .
	docker run --rm --security-opt label=disable \
	    -v `pwd`/dist/:/host kiwitcms/xmlsec-buildroot /bin/bash -c 'cp /dist/*.whl /host/'
	docker rmi kiwitcms/xmlsec-buildroot


.PHONY: docker-image
docker-image: build build-gssapi build-xmlsec
	# everything else below is Enterprise + multi-tenant
	docker build --build-arg KIWI_VERSION=$(KIWI_VERSION) -t hub.kiwitcms.eu/kiwitcms/enterprise:$(ENTERPRISE_VERSION)-$(shell uname -m) .


.PHONY: test-docker-image
test-docker-image: docker-image
	docker tag hub.kiwitcms.eu/kiwitcms/enterprise:$(ENTERPRISE_VERSION)-$(shell uname -m) hub.kiwitcms.eu/kiwitcms/enterprise:latest
	./testing/runner.sh


.PHONY: extract-static-files
extract-static-files:
	# warning: requires a running container
	docker cp web:/Kiwi/static /var/tmp/extracted.static/
	find /var/tmp/extracted.static/ -type l -exec rm '{}' \;
	find /var/tmp/extracted.static/ -type f | sort
	find /var/tmp/extracted.static/ -type f | wc -l


.PHONY: docker-manifest
docker-manifest:
	# versioned manifest
	docker manifest rm quay.io/kiwitcms/enterprise:$(ENTERPRISE_VERSION) || echo
	docker manifest create \
	    quay.io/kiwitcms/enterprise:$(ENTERPRISE_VERSION) \
	    quay.io/kiwitcms/enterprise:$(ENTERPRISE_VERSION)-x86_64 \
	    quay.io/kiwitcms/enterprise:$(ENTERPRISE_VERSION)-aarch64
	docker manifest push quay.io/kiwitcms/enterprise:$(ENTERPRISE_VERSION)

	# latest manifest
	docker manifest rm quay.io/kiwitcms/enterprise:latest || echo
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
	    pip install -U -r $(KIWI_LINT_INCLUDE_PATH)/requirements/base.txt; \
	    pip install -U -r requirements.txt; \
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
