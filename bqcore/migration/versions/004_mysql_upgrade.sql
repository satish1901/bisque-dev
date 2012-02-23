
BEGIN;


alter table taggable drop foreign key taggable_ibfk_1;
alter table taggable drop column tb_id;


alter table taggable change column mex mex_id;
alter table values  change column  parent_id resource_parent_id;
alter table vertices  change column  parent_id resource_parent_id;

drop table services;
drop table dataset;
drop table mex;
drop table modules;
drop table templates;
drop table groups;
drop table users;
drop table images;
drop table gobjects;
drop table tags;
drop table names;
drop table files_acl;
drop table files;

create index resource_document_idx on taggable (document_id);
create index resource_parent_idx on taggable (resource_parent_id);
create index resource_type_idx on taggable (resource_type);

commit;

