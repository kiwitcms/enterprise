# *WARNING:* don't forget to update version in setup.py
KIWI_VERSION=8.6
ENTERPRISE_VERSION=$(KIWI_VERSION)-mt

.PHONY: build
build:
	rm -rf dist/ build/ *.egg-info/
	python setup.py sdist
	python setup.py bdist_wheel
	twine check dist/*

.PHONY: docker-image
docker-image: build
	# everything else below is Enterprise + multi-tenant
	docker build -t quay.io/kiwitcms/enterprise:$(ENTERPRISE_VERSION) .
	docker tag quay.io/kiwitcms/enterprise:$(ENTERPRISE_VERSION) quay.io/kiwitcms/enterprise:latest

	# keep tagging & pushing to Docker Hub during grace period
	docker tag quay.io/kiwitcms/enterprise:$(ENTERPRISE_VERSION) mrsenko/kiwitcms-enterprise:$(ENTERPRISE_VERSION)
	docker tag quay.io/kiwitcms/enterprise:latest mrsenko/kiwitcms-enterprise:latest

	# tag the regular version so we can provide versioned images to enterprise customers
	# so they can upgrade from kiwitcms/kiwi:latest before migrating to kiwitcms-enteprise
	docker tag kiwitcms/kiwi:latest mrsenko/kiwitcms:$(KIWI_VERSION)
	docker tag kiwitcms/kiwi:latest quay.io/kiwitcms/version:$(KIWI_VERSION)


.PHONY: flake8
flake8:
	@flake8 --exclude=.git *.py tcms_enterprise tcms_settings_dir

KIWI_LINT_INCLUDE_PATH="../Kiwi"

.PHONY: pylint
pylint:
	if [ ! -d "$(KIWI_LINT_INCLUDE_PATH)/kiwi_lint" ]; then \
	    git clone --depth 1 https://github.com/kiwitcms/Kiwi.git $(KIWI_LINT_INCLUDE_PATH); \
	fi

	PYTHONPATH=$(KIWI_LINT_INCLUDE_PATH) \
	pylint --load-plugins=pylint_django --load-plugins=kiwi_lint \
	    -d missing-docstring -d duplicate-code -d module-in-directory-without-init \
	    *.py tcms_enterprise/ tcms_settings_dir/

.PHONY: messages
messages:
	./manage.py makemessages --settings l10n_settings --locale en --no-obsolete --ignore "test*.py"
	ls tcms_enterprise/locale/*/LC_MESSAGES/*.po | xargs -n 1 -I @ msgattrib -o @ --no-fuzzy @
