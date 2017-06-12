osname := $(shell uname)
today := $(shell /bin/date "+%Y-%m-%d")
current := $(today)/$(shell /bin/date "+%Y-%m-%d-%H-%M-%S")


container_name := $(shell basename `pwd`|tr -cd "[a-z][A-Z]")

container_mariadb_instance := ${container_name}_mariadb_1

mariadb_data_dir := container-data/mariadb/_PERSISTENT_/_var_lib_mysql
mariadb_init_dir := container-data/mariadb/INITDB




define exec_cmd_result
	-@$(1) 2>/dev/null && ([ $$? -eq 0 ] && echo "success!") || echo "failure!" 	
endef

ifeq ("${osname}","Darwin")
	SED := gsed
else
	SED := sed
endif



default:
	@echo 'please give me a task'
	@echo "${container_name}"
all:
	make clean
	make reset_mariadb
	make build
	make dev
build:
	docker-compose build --no-cache
dev_after_build:
	docker-compose up --build
dev:
	docker-compose up --no-build
ready_all:
	make reset_mariadb

reset_mariadb:
	@echo 'rm mariadb persistent'
	rm -rf ${mariadb_data_dir}/*
	rm -rf ${mariadb_init_dir}/*
rm_dangling:
	@echo 'rm dangling container'
	$(call exec_cmd_result,docker rmi -f $$(docker images -f dangling=true -q))
kill_all_containers:
	@echo 'kill all containers'
	$(call exec_cmd_result,docker kill $$(docker ps -q))

rm_all_containers:
	@echo 'rm all containers'
	$(call exec_cmd_result ,docker rm $$(docker ps -aq))

rm_all_images:
	@echo 'rm all images'
	$(call exec_cmd_result ,docker rmi -f $$(docker images -aq)) 
rm_all_volumes:
	@echo 'rm all volumes'
	$(call exec_cmd_result ,docker volume rm $$(docker volume ls -qf dangling=true))

clean:
	@echo 'clean starting'
	-make kill_all_containers
	-make rm_all_containers
	-make rm_all_images
	-make rm_all_volumes
	@echo 'clean end'
ds_store:
	find . -name ".DS_Store" -delete
sync_db:
	docker exec ${container_mariadb_instance} mysqldump -uroot -p${env_db_password} ${env_db_database} > ${env_db_database}.sql
	${SED} -i "1iDROP DATABASE IF EXISTS ${env_db_database};" ${env_db_database}.sql
	${SED} -i "2iCREATE DATABASE IF NOT EXISTS ${env_db_database};" ${env_db_database}.sql
	${SED} -i "3iUSE ${env_db_database};" ${env_db_database}.sql
	mv ${env_db_database}.sql ${mariadb_init_dir}
sync:
	@echo 'make sure all dockers run'
	-make sync_db
deploy:
	@echo 'git pull ?'
	@echo 'mariadb docker must run'
	-make deploy_db
deploy_db:
	docker exec -i ${container_mariadb_instance} mysql -uroot -p${env_db_password} < ${mariadb_init_dir}/${env_db_database}.sql




