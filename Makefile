# *WARNING:* don't forget to update version in setup.py
KIWI_VERSION=8.3-mt

.PHONY: build
build:
	rm -rf dist/ build/ *.egg-info/
	python setup.py sdist
	python setup.py bdist_wheel
	twine check dist/*

.PHONY: docker-image
docker-image: build
	docker build -t docker.io/mrsenko/kiwitcms-enterprise:$(KIWI_VERSION) .
	docker tag docker.io/mrsenko/kiwitcms-enterprise:$(KIWI_VERSION) docker.io/mrsenko/kiwitcms-enterprise:latest

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
