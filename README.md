Docker compose for KiwiTestPad
==============================

This is a docker compose to help you install and configure the
[KiwiTestPad](https://github.com/MrSenko/Kiwi/) test case management
system when running as a Docker container.


Create Docker container
-----------------------

Before you start you will need the `mrsenko/kiwi:<version>` image pulled
locally. Alternatively you have to build it yourself!

You can then start using KiwiTestPad by executing:

    docker-compose up -d

This will create two containers:

1) A web container based on the latest KiwiTestPad image
2) A DB container based on the official centos/mariadb image


`docker-compose` will also create two volumes for persistent data storage:
`kiwi_db_data` and `kiwi_uploads`.


Initial configuration of running container
------------------------------------------

You need to do initial configuration by executing:

    docker exec -it kiwi_web_1 /Kiwi/manage.py migrate
    docker exec -it kiwi_web_1 /Kiwi/manage.py createsuperuser

Upgrading
---------

To upgrade running KiwiTestPad containers execute the following commands::

    docker-compose stop
    docker rm kiwi_web_1 kiwi_db_1
    docker pull # to fetch latest version from Docker.io
    docker-compose up -d
    docker exec -it kiwi_web_1 /Kiwi/manage.py migrate

.. note::
    Uploads and database data should stay intact because they are split into
    separate volumes, which makes upgrading very easy. However you may want to
    back these up before upgrading!
